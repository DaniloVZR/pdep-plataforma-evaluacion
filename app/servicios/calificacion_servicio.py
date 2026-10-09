"""Caso de uso HU-007: calificar un proyecto con la rúbrica digital."""

from app.dominio.errores import (
    EvaluacionYaConfirmadaError,
    EvaluadorNoAsignadoError,
    RubricaNoEncontradaError,
)
from app.dominio.modelos import EstadoEvaluacion, Evaluacion
from app.repositorios.contratos import EvaluacionRepositorio, RubricaRepositorio
from app.servicios.reloj import Reloj
from app.validadores.calificacion_validador import (
    validar_notas_completas,
    validar_rubrica,
    validar_solicitud_calificacion,
)


class CalificacionServicio:
    """Coordina la validación de la rúbrica, el cálculo del puntaje y el cierre."""

    def __init__(self, evaluacion_repo: EvaluacionRepositorio,
                 rubrica_repo: RubricaRepositorio, reloj: Reloj) -> None:
        self._evaluacion_repo = evaluacion_repo
        self._rubrica_repo = rubrica_repo
        self._reloj = reloj

    def calificar(self, proyecto_id: int, datos: object) -> Evaluacion:
        """Valida, calcula Σ (nota × peso) y guarda en borrador o confirmada.

        El cálculo recorre los criterios una sola vez y no consulta la base de
        datos dentro del ciclo (RNF-01).
        """
        evaluador_id, notas, confirmar = validar_solicitud_calificacion(datos)   # D1
        evaluacion = self._evaluacion_repo.obtener_asignada(evaluador_id, proyecto_id)
        if evaluacion is None:                                                   # D2
            raise EvaluadorNoAsignadoError("El evaluador no tiene asignado este proyecto.")
        if evaluacion.estado is EstadoEvaluacion.CONFIRMADA:                     # D3
            raise EvaluacionYaConfirmadaError("La evaluación ya fue confirmada.")
        rubrica = self._rubrica_repo.obtener_por_feria(evaluacion.feria_id)
        if rubrica is None:                                                      # D4
            raise RubricaNoEncontradaError("La feria no tiene una rúbrica asociada.")
        validar_rubrica(rubrica)                                                 # D5, D6
        validar_notas_completas(rubrica, notas)                                  # D7
        puntaje = rubrica.calcular_puntaje(notas)                                # D8, D9, D10
        notas_validas = {criterio_id: float(nota) for criterio_id, nota in notas.items()}
        calificada = evaluacion.con_calificacion(notas_validas, puntaje,
                                                 confirmada=confirmar,           # D11
                                                 momento=self._reloj.ahora())
        return self._evaluacion_repo.guardar_calificacion(calificada)
