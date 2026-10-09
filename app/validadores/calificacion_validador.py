"""Validaciones de la calificación con rúbrica (HU-007)."""

from app.dominio.errores import (
    DatoInvalidoError,
    NotasIncompletasError,
    PesosInvalidosError,
    RubricaSinCriteriosError,
)
from app.dominio.modelos import Rubrica
from app.validadores.comunes import es_entero_positivo


def validar_solicitud_calificacion(datos: object) -> tuple[int, dict[int, object], bool]:
    """Valida la forma de la solicitud y devuelve ``(evaluador_id, notas, confirmar)``.

    Las claves de ``notas`` llegan como texto desde JSON (``{"7": 4.5}``) y se
    convierten a entero. El valor de cada nota no se revisa aquí: lo revisa
    ``Rubrica.validar_nota`` dentro del ciclo de cálculo.
    """
    if not isinstance(datos, dict):
        raise DatoInvalidoError("El cuerpo de la solicitud debe ser un objeto JSON.")
    evaluador_id = datos.get("evaluador_id")
    notas = datos.get("notas")
    confirmar = datos.get("confirmar", False)
    if not es_entero_positivo(evaluador_id):
        raise DatoInvalidoError("El campo 'evaluador_id' debe ser un entero positivo.")
    if not isinstance(notas, dict) or not notas:
        raise DatoInvalidoError("El campo 'notas' debe ser un objeto con al menos una nota.")
    if not isinstance(confirmar, bool):
        raise DatoInvalidoError("El campo 'confirmar' debe ser true o false.")
    try:
        notas_por_criterio = {int(clave): valor for clave, valor in notas.items()}
    except ValueError as error:
        raise DatoInvalidoError("Las claves de 'notas' deben ser ids de criterio.") from error
    return evaluador_id, notas_por_criterio, confirmar


def validar_rubrica(rubrica: Rubrica) -> None:
    """La rúbrica debe tener criterios y pesos positivos que sumen 1."""
    if not rubrica.criterios:
        raise RubricaSinCriteriosError("La rúbrica de la feria no tiene criterios.")
    if not rubrica.pesos_validos():
        raise PesosInvalidosError("Los pesos de la rúbrica deben ser positivos y sumar 100 %.")


def validar_notas_completas(rubrica: Rubrica, notas: dict[int, object]) -> None:
    """Debe haber exactamente una nota por cada criterio, ni más ni menos."""
    if set(notas) != rubrica.ids_criterios():
        raise NotasIncompletasError("Debe enviar exactamente una nota por cada criterio.")
