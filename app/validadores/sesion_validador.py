"""Validaciones del inicio de sesión (RNF-03)."""

from app.dominio.errores import DatoInvalidoError
from app.validadores.comunes import es_texto_no_vacio


def validar_datos_login(datos: object) -> None:
    """Lanza ``DatoInvalidoError`` si falta el correo o la contraseña, o no son texto."""
    if not isinstance(datos, dict):
        raise DatoInvalidoError("El cuerpo de la solicitud debe ser un objeto JSON.")
    for campo in ("correo", "clave"):
        if not es_texto_no_vacio(datos.get(campo)):
            raise DatoInvalidoError(f"El campo '{campo}' es obligatorio y debe ser texto.")
