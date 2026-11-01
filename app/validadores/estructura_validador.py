"""Validaciones del registro de la estructura académica (HU-001)."""

from app.dominio.errores import DatoInvalidoError
from app.validadores.comunes import es_entero_positivo, es_texto_no_vacio


def _exigir_objeto(datos: object) -> None:
    if not isinstance(datos, dict):
        raise DatoInvalidoError("El cuerpo de la solicitud debe ser un objeto JSON.")


def _exigir_texto(datos: dict, campo: str, mensaje: str) -> None:
    if not es_texto_no_vacio(datos.get(campo)):
        raise DatoInvalidoError(mensaje)


def _exigir_texto_opcional(datos: dict, campo: str) -> None:
    if not isinstance(datos.get(campo, ""), str):
        raise DatoInvalidoError(f"El campo '{campo}' debe ser texto.")


def _exigir_id(datos: dict, campo: str) -> None:
    if not es_entero_positivo(datos.get(campo)):
        raise DatoInvalidoError(f"El campo '{campo}' debe ser un entero positivo.")


def _exigir_id_opcional(datos: dict, campo: str) -> None:
    valor = datos.get(campo)
    if valor is not None and not es_entero_positivo(valor):
        raise DatoInvalidoError(f"El campo '{campo}' debe ser un entero positivo.")


def limpiar_texto(texto: str) -> str:
    """Quita espacios al inicio y al final y deja uno solo entre palabras."""
    return " ".join(texto.split())


def dominio_valido(dominio: str) -> bool:
    """``"pascualbravo.edu.co"`` es válido; ``"ana@x.co"``, ``"sin punto"`` y ``""`` no."""
    return "." in dominio and "@" not in dominio and " " not in dominio


def validar_datos_institucion(datos: object) -> None:
    """REQ-1: ``nombre`` y ``nit`` obligatorios; contacto y dominio son opcionales."""
    _exigir_objeto(datos)
    _exigir_texto(datos, "nombre", "El nombre de la institución es obligatorio.")
    _exigir_texto(datos, "nit", "El NIT (identificación) de la institución es obligatorio.")
    for campo in ("correo_contacto", "telefono", "dominio"):
        _exigir_texto_opcional(datos, campo)
    dominio = datos.get("dominio", "").strip()
    if dominio and not dominio_valido(dominio):
        raise DatoInvalidoError("El dominio debe tener la forma 'institucion.edu.co', sin '@'.")


MENSAJE_SIN_NOMBRE = {
    "facultad": "El nombre de la facultad es obligatorio.",
    "departamento": "El nombre del departamento es obligatorio.",
}


def validar_datos_unidad(datos: object, unidad: str) -> None:
    """REQ-2: ``unidad`` (``"facultad"`` o ``"departamento"``) con ``institucion_id`` y
    ``nombre`` obligatorios."""
    _exigir_objeto(datos)
    _exigir_id(datos, "institucion_id")
    _exigir_texto(datos, "nombre", MENSAJE_SIN_NOMBRE[unidad])


def validar_datos_programa(datos: object) -> None:
    """REQ-3: el programa necesita facultad o departamento (puede tener los dos)."""
    _exigir_objeto(datos)
    _exigir_id(datos, "institucion_id")
    _exigir_texto(datos, "codigo", "El código del programa es obligatorio.")
    _exigir_texto(datos, "nombre", "El nombre del programa es obligatorio.")
    _exigir_id_opcional(datos, "facultad_id")
    _exigir_id_opcional(datos, "departamento_id")
    if datos.get("facultad_id") is None and datos.get("departamento_id") is None:
        raise DatoInvalidoError("El programa debe pertenecer a una facultad o a un departamento.")
