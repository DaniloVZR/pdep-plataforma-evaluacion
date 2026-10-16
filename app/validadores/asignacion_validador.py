"""Validaciones de la asignación de evaluadores (HU-006)."""

from app.dominio.errores import DatoInvalidoError
from app.validadores.comunes import es_lista_de_ids


def validar_datos_asignacion(datos: object) -> None:
    """``evaluador_ids`` debe ser una lista no vacía de enteros positivos, sin repetidos.

    Un id repetido en la misma solicitud sería asignar dos veces al mismo evaluador
    (REQ-12), así que se rechaza antes de consultar la base de datos.
    """
    if not isinstance(datos, dict):
        raise DatoInvalidoError("El cuerpo de la solicitud debe ser un objeto JSON.")
    ids = datos.get("evaluador_ids")
    if not es_lista_de_ids(ids) or not ids:
        raise DatoInvalidoError("'evaluador_ids' debe ser una lista no vacía de enteros "
                                "positivos.")
    if len(set(ids)) != len(ids):
        raise DatoInvalidoError("'evaluador_ids' tiene evaluadores repetidos.")
