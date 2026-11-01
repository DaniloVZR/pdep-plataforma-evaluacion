"""Validaciones del registro de asignaturas (HU-002)."""

from app.dominio.errores import DatoInvalidoError
from app.validadores.comunes import es_entero_positivo, es_texto_no_vacio


def validar_datos_asignatura(datos: object) -> None:
    """REQ-4: ``programa_id``, ``codigo``, ``nombre`` y ``semestre`` son obligatorios.

    ``programa_id`` y ``semestre`` deben ser enteros mayores que 0 (``true`` no cuenta).
    """
    if not isinstance(datos, dict):
        raise DatoInvalidoError("El cuerpo de la solicitud debe ser un objeto JSON.")
    if not es_entero_positivo(datos.get("programa_id")):
        raise DatoInvalidoError("Debe seleccionar el programa académico de la asignatura.")
    if not es_texto_no_vacio(datos.get("codigo")):
        raise DatoInvalidoError("El código de la asignatura es obligatorio.")
    if not es_texto_no_vacio(datos.get("nombre")):
        raise DatoInvalidoError("El nombre de la asignatura es obligatorio.")
    if not es_entero_positivo(datos.get("semestre")):
        raise DatoInvalidoError("El campo 'semestre' debe ser un entero positivo.")
