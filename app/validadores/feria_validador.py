"""Validaciones de la creación de ferias (HU-004)."""

from datetime import date
import math

from app.dominio.errores import DatoInvalidoError
from app.validadores.comunes import es_entero_positivo, es_lista_de_ids, es_texto_no_vacio


def leer_fecha(valor: object) -> date | None:
    """``"2026-11-20"`` → ``date(2026, 11, 20)``; cualquier otra cosa → ``None``."""
    if not isinstance(valor, str):
        return None
    try:
        return date.fromisoformat(valor.strip())
    except ValueError:
        return None


def es_peso(valor: object) -> bool:
    """Número finito y positivo. ``bool`` se excluye aunque en Python sea ``int``."""
    return (isinstance(valor, (int, float)) and not isinstance(valor, bool)
            and math.isfinite(valor) and valor > 0)


def validar_datos_feria(datos: object) -> None:
    """Forma de la solicitud: institución, nombre, fechas, asignaturas y criterios (REQ-7).

    Que la fecha de fin sea posterior a la de inicio y que los pesos sumen 1 son reglas de
    negocio; las revisa el servicio después de esta validación.
    """
    if not isinstance(datos, dict):
        raise DatoInvalidoError("El cuerpo de la solicitud debe ser un objeto JSON.")
    if not es_entero_positivo(datos.get("institucion_id")):
        raise DatoInvalidoError("El campo 'institucion_id' debe ser un entero positivo.")
    if not es_texto_no_vacio(datos.get("nombre")):
        raise DatoInvalidoError("El nombre de la feria es obligatorio.")
    for campo in ("fecha_inicio", "fecha_fin"):
        if leer_fecha(datos.get(campo)) is None:
            raise DatoInvalidoError(f"El campo '{campo}' debe ser una fecha AAAA-MM-DD.")
    asignaturas = datos.get("asignatura_ids")
    if not es_lista_de_ids(asignaturas) or not asignaturas:
        raise DatoInvalidoError("Elija al menos una asignatura participante.")
    if len(set(asignaturas)) != len(asignaturas):
        raise DatoInvalidoError("'asignatura_ids' tiene asignaturas repetidas.")
    validar_criterios(datos.get("criterios"))


def validar_criterios(criterios: object) -> None:
    """Lista no vacía de ``{"nombre", "peso"}`` con nombres distintos y pesos positivos."""
    if not isinstance(criterios, list) or not criterios:
        raise DatoInvalidoError("La feria necesita al menos un criterio de evaluación.")
    nombres = set()
    for criterio in criterios:
        if not isinstance(criterio, dict) or not es_texto_no_vacio(criterio.get("nombre")):
            raise DatoInvalidoError("Cada criterio necesita un nombre.")
        if not es_peso(criterio.get("peso")):
            raise DatoInvalidoError("El peso de cada criterio debe ser un número mayor que 0.")
        nombre = " ".join(criterio["nombre"].split()).lower()
        if nombre in nombres:
            raise DatoInvalidoError("Hay dos criterios con el mismo nombre.")
        nombres.add(nombre)
