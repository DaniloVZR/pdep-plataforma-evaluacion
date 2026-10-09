"""Validaciones del registro de usuarios (HU-003)."""

from app.dominio.errores import DatoInvalidoError
from app.dominio.modelos import Rol
from app.validadores.comunes import es_entero_positivo, es_lista_de_ids, es_texto_no_vacio

CAMPOS_TEXTO = ("nombres", "correo", "rol")


def validar_datos_registro(datos: object) -> None:
    """Lanza ``DatoInvalidoError`` si falta un campo o tiene un tipo incorrecto.

    Revisa, en orden: que el cuerpo sea un diccionario, que ``nombres``,
    ``correo`` y ``rol`` sean texto no vacío, que el rol sea ESTUDIANTE o
    DOCENTE, que ``programa_id`` sea un entero positivo y que
    ``asignatura_ids``, si viene, sea una lista de enteros positivos.
    """
    if not isinstance(datos, dict):
        raise DatoInvalidoError("El cuerpo de la solicitud debe ser un objeto JSON.")
    for campo in CAMPOS_TEXTO:
        if not es_texto_no_vacio(datos.get(campo)):
            raise DatoInvalidoError(f"El campo '{campo}' es obligatorio y debe ser texto.")
    if datos["rol"].strip().upper() not in {rol.value for rol in Rol}:
        raise DatoInvalidoError("El rol debe ser ESTUDIANTE o DOCENTE.")
    if not es_entero_positivo(datos.get("programa_id")):
        raise DatoInvalidoError("El campo 'programa_id' debe ser un entero positivo.")
    if not es_lista_de_ids(datos.get("asignatura_ids", [])):
        raise DatoInvalidoError("'asignatura_ids' debe ser una lista de enteros positivos.")


def normalizar_correo(correo: str) -> str:
    """Quita espacios y pasa a minúsculas para que la comparación sea exacta."""
    return correo.strip().lower()


def extraer_dominio(correo: str) -> str:
    """Devuelve lo que va después de la única ``@``, o ``""`` si el correo no es válido.

    ``"ana@pascualbravo.edu.co"`` → ``"pascualbravo.edu.co"``.
    ``"ana@b@pascualbravo.edu.co"``, ``"@pascualbravo.edu.co"`` y ``"ana"`` → ``""``.
    """
    if correo.count("@") != 1:
        return ""
    usuario, _, dominio = correo.partition("@")
    if not usuario:
        return ""
    return dominio


def dominio_es_institucional(correo: str, dominios: frozenset[str]) -> bool:
    """Compara el dominio de forma exacta con los dominios registrados (RN001).

    ``"ana@pascualbravo.edu.co.falso.com"`` no pasa: no basta con que el
    correo *contenga* el dominio.
    """
    dominio = extraer_dominio(correo)
    return dominio != "" and dominio in dominios
