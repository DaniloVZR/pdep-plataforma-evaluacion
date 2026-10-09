"""HU-007 · Caminos de ``CalificacionServicio.calificar``. V(G) = 12."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.dominio.errores import (
    DatoInvalidoError,
    EvaluacionYaConfirmadaError,
    EvaluadorNoAsignadoError,
    NotaFueraDeRangoError,
    NotasIncompletasError,
    PesosInvalidosError,
    RubricaNoEncontradaError,
    RubricaSinCriteriosError,
    TipoNotaInvalidoError,
)
from app.dominio.modelos import Criterio, EstadoEvaluacion, Evaluacion, Rubrica
from app.repositorios.contratos import EvaluacionRepositorio, RubricaRepositorio
from app.servicios.calificacion_servicio import CalificacionServicio

CRITERIOS = (Criterio(1, "Funcionalidad", 0.5), Criterio(2, "Código", 0.3),
             Criterio(3, "Presentación", 0.2))
RUBRICA = Rubrica(id=4, feria_id=7, nota_minima=1.0, nota_maxima=5.0, criterios=CRITERIOS)
RUBRICA_UN_CRITERIO = Rubrica(id=5, feria_id=7, nota_minima=1.0, nota_maxima=5.0,
                              criterios=(Criterio(1, "Global", 1.0),))
PENDIENTE = Evaluacion(id=9, proyecto_id=50, evaluador_id=2, feria_id=7,
                       estado=EstadoEvaluacion.PENDIENTE)


@pytest.fixture(name="repos")
def fixture_repos():
    """Repositorios simulados configurados para el camino exitoso."""
    evaluacion_repo = Mock(spec=EvaluacionRepositorio)
    evaluacion_repo.obtener_asignada.return_value = PENDIENTE
    evaluacion_repo.guardar_calificacion.side_effect = lambda evaluacion: evaluacion
    rubrica_repo = Mock(spec=RubricaRepositorio)
    rubrica_repo.obtener_por_feria.return_value = RUBRICA
    return SimpleNamespace(evaluacion=evaluacion_repo, rubrica=rubrica_repo)


@pytest.fixture(name="servicio")
def fixture_servicio(repos, reloj_fijo):
    """Servicio con repositorios simulados y reloj fijo el 9 de octubre de 2026."""
    return CalificacionServicio(repos.evaluacion, repos.rubrica, reloj_fijo(date(2026, 10, 9)))


def solicitud(notas=None, confirmar=True, evaluador_id=2):
    """Cuerpo JSON de la solicitud; las claves de ``notas`` llegan como texto."""
    notas = {"1": 4.0, "2": 3.0, "3": 5.0} if notas is None else notas
    return {"evaluador_id": evaluador_id, "notas": notas, "confirmar": confirmar}


def test_c1_solicitud_mal_formada(servicio, repos):
    """C1: 1→2→3→31→32. ``confirmar`` llega como texto."""
    with pytest.raises(DatoInvalidoError):
        servicio.calificar(50, solicitud(confirmar="true"))
    repos.evaluacion.obtener_asignada.assert_not_called()


def test_c2_evaluador_no_asignado(servicio, repos):
    """C2: 1→2→4→5→6→31→32 (RNF-03)."""
    repos.evaluacion.obtener_asignada.return_value = None
    with pytest.raises(EvaluadorNoAsignadoError):
        servicio.calificar(50, solicitud(evaluador_id=99))
    repos.rubrica.obtener_por_feria.assert_not_called()


def test_c3_evaluacion_ya_confirmada(servicio, repos):
    """C3: 1→2→4→5→7→8→31→32. Una evaluación confirmada no se modifica (RN007)."""
    repos.evaluacion.obtener_asignada.return_value = Evaluacion(
        id=9, proyecto_id=50, evaluador_id=2, feria_id=7,
        estado=EstadoEvaluacion.CONFIRMADA, puntaje_final=3.9)
    with pytest.raises(EvaluacionYaConfirmadaError):
        servicio.calificar(50, solicitud())
    repos.evaluacion.guardar_calificacion.assert_not_called()


def test_c4_feria_sin_rubrica(servicio, repos):
    """C4: 1→2→4→5→7→9→10→11→31→32 (RN005)."""
    repos.rubrica.obtener_por_feria.return_value = None
    with pytest.raises(RubricaNoEncontradaError):
        servicio.calificar(50, solicitud())
    repos.evaluacion.guardar_calificacion.assert_not_called()


def test_c5_rubrica_sin_criterios(servicio, repos):
    """C5: 1→…→10→12→13→31→32."""
    repos.rubrica.obtener_por_feria.return_value = Rubrica(4, 7, 1.0, 5.0, ())
    with pytest.raises(RubricaSinCriteriosError):
        servicio.calificar(50, solicitud())


def test_c6_pesos_que_no_suman_uno(servicio, repos):
    """C6: 1→…→12→14→15→31→32. Pesos 0.5 + 0.3 = 0.8."""
    repos.rubrica.obtener_por_feria.return_value = Rubrica(
        4, 7, 1.0, 5.0, (Criterio(1, "A", 0.5), Criterio(2, "B", 0.3)))
    with pytest.raises(PesosInvalidosError):
        servicio.calificar(50, solicitud(notas={"1": 4, "2": 4}))


def test_c7_falta_la_nota_de_un_criterio(servicio):
    """C7: 1→…→14→16→17→31→32. Llegan notas de 2 de los 3 criterios."""
    with pytest.raises(NotasIncompletasError):
        servicio.calificar(50, solicitud(notas={"1": 4.0, "2": 3.0}))


def test_c8_nota_de_tipo_texto(servicio, repos):
    """C8: 1→…→16→18→19→20→21→31→32. ``"4.5"`` (string) en el primer criterio."""
    with pytest.raises(TipoNotaInvalidoError):
        servicio.calificar(50, solicitud(notas={"1": "4.5", "2": 3.0, "3": 5.0}))
    repos.evaluacion.guardar_calificacion.assert_not_called()


def test_c9_nota_fuera_de_rango(servicio, repos):
    """C9: 1→…→19→20→22→23→31→32. 5.01 supera la nota máxima 5.0."""
    with pytest.raises(NotaFueraDeRangoError):
        servicio.calificar(50, solicitud(notas={"1": 5.01, "2": 3.0, "3": 5.0}))
    repos.evaluacion.guardar_calificacion.assert_not_called()


def test_c10_un_criterio_sin_confirmar_queda_en_borrador(servicio, repos):
    """C10: …→19→20→22→24→19→25→26→27→29→30→32. Una vuelta del ciclo."""
    repos.rubrica.obtener_por_feria.return_value = RUBRICA_UN_CRITERIO
    evaluacion = servicio.calificar(50, solicitud(notas={"1": 4.5}, confirmar=False))
    assert evaluacion.estado is EstadoEvaluacion.BORRADOR
    assert evaluacion.puntaje_final == 4.5
    assert evaluacion.puntaje_visible is None
    assert evaluacion.fecha_confirmacion is None


def test_c11_un_criterio_confirmado(servicio, repos):
    """C11: …→19→20→22→24→19→25→26→28→29→30→32."""
    repos.rubrica.obtener_por_feria.return_value = RUBRICA_UN_CRITERIO
    evaluacion = servicio.calificar(50, solicitud(notas={"1": 4.5}))
    assert evaluacion.estado is EstadoEvaluacion.CONFIRMADA
    assert evaluacion.puntaje_visible == 4.5


def test_c12_varios_criterios_confirmado(servicio, repos):
    """C12: el ciclo da tres vueltas. 4.0×0.5 + 3.0×0.3 + 5.0×0.2 = 3.9 (RN006)."""
    evaluacion = servicio.calificar(50, solicitud())
    assert evaluacion.puntaje_visible == 3.9
    assert evaluacion.notas == {1: 4.0, 2: 3.0, 3: 5.0}
    assert evaluacion.fecha_confirmacion.isoformat() == "2026-10-09T10:30:00-05:00"
    repos.evaluacion.obtener_asignada.assert_called_once_with(2, 50)
    repos.evaluacion.guardar_calificacion.assert_called_once()


def test_nota_invalida_en_el_ultimo_criterio_tambien_corta_el_ciclo(servicio, repos):
    """Variante de C9 en la tercera vuelta del ciclo: no se guarda nada."""
    with pytest.raises(NotaFueraDeRangoError):
        servicio.calificar(50, solicitud(notas={"1": 4.0, "2": 3.0, "3": 0.99}))
    repos.evaluacion.guardar_calificacion.assert_not_called()
