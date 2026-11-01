"""HU-009 · Caminos de ``ConsultaResultadosServicio.consultar`` y del campo
``retroalimentacion`` que HU-007 guarda.

El repositorio es ``Mock(spec=ResultadoRepositorio)``: no hay base de datos.
"""

from datetime import date, datetime
from unittest.mock import Mock

import pytest

from app.dominio.errores import (
    DatoInvalidoError,
    UsuarioNoEncontradoError,
    UsuarioNoEstudianteError,
)
from app.dominio.modelos import (
    Criterio,
    EstadoEvaluacion,
    Evaluacion,
    ResultadoEvaluacion,
    ResultadoProyecto,
    Rubrica,
)
from app.repositorios.contratos import (
    EvaluacionRepositorio,
    ResultadoRepositorio,
    RubricaRepositorio,
)
from app.servicios.calificacion_servicio import CalificacionServicio
from app.servicios.resultado_servicio import ConsultaResultadosServicio
from app.validadores.calificacion_validador import leer_retroalimentacion

MOMENTO = datetime(2026, 10, 30, 9, 0)
CONFIRMADA = ResultadoEvaluacion(1, "Docente Evaluador", EstadoEvaluacion.CONFIRMADA, 3.9,
                                 "Buen trabajo; mejorar la presentación.", MOMENTO)
BORRADOR = ResultadoEvaluacion(2, "Otra Docente", EstadoEvaluacion.BORRADOR, 2.5,
                               "Texto aún sin confirmar", None)
PENDIENTE = ResultadoEvaluacion(3, "Tercer Docente", EstadoEvaluacion.PENDIENTE, None, "", None)


@pytest.fixture(name="repo")
def fixture_repo():
    """El usuario es estudiante y tiene un proyecto con tres evaluaciones en estados distintos,
    y otro proyecto todavía sin evaluadores."""
    repo = Mock(spec=ResultadoRepositorio)
    repo.rol_de_usuario.return_value = "ESTUDIANTE"
    repo.resultados_de_estudiante.return_value = (
        ResultadoProyecto(1, "Proyecto Demo", "Feria 2026-2", "Equipo Demo",
                          (CONFIRMADA, BORRADOR, PENDIENTE)),
        ResultadoProyecto(2, "Sin evaluar", "Feria 2026-2", "Equipo Demo"),
    )
    return repo


@pytest.fixture(name="servicio")
def fixture_servicio(repo):
    """Servicio con el repositorio simulado."""
    return ConsultaResultadosServicio(repo)


@pytest.mark.parametrize("estudiante_id", [None, 0, -3, True, "2"])
def test_d1_id_invalido_no_consulta_la_base(servicio, repo, estudiante_id):
    """D1 verdadero: 400 sin tocar el repositorio."""
    with pytest.raises(DatoInvalidoError, match="estudiante_id"):
        servicio.consultar(estudiante_id)
    repo.rol_de_usuario.assert_not_called()


def test_d2_usuario_inexistente(servicio, repo):
    """D2 verdadero: 404."""
    repo.rol_de_usuario.return_value = None
    with pytest.raises(UsuarioNoEncontradoError):
        servicio.consultar(99)
    repo.resultados_de_estudiante.assert_not_called()


def test_d3_un_docente_no_consulta_resultados(servicio, repo):
    """D3 verdadero: 422 (RNF-03)."""
    repo.rol_de_usuario.return_value = "DOCENTE"
    with pytest.raises(UsuarioNoEstudianteError):
        servicio.consultar(1)
    repo.resultados_de_estudiante.assert_not_called()


def test_rn007_solo_se_publica_la_evaluacion_confirmada(servicio, repo):
    """D4 y D5: la confirmada sale completa; borrador y pendiente sin puntaje ni texto."""
    proyecto, sin_evaluar = servicio.consultar(2)
    repo.resultados_de_estudiante.assert_called_once_with(2)
    confirmada, borrador, pendiente = proyecto.evaluaciones
    assert confirmada == CONFIRMADA
    assert (borrador.estado, borrador.puntaje_final, borrador.retroalimentacion) == \
        (EstadoEvaluacion.BORRADOR, None, None)
    assert (pendiente.puntaje_final, pendiente.retroalimentacion) == (None, None)
    assert sin_evaluar.evaluaciones == ()


def test_estudiante_sin_proyectos(servicio, repo):
    """D4 con cero proyectos: tupla vacía."""
    repo.resultados_de_estudiante.return_value = ()
    assert servicio.consultar(2) == ()


# ───────────── Retroalimentación que guarda HU-007 ─────────────

@pytest.mark.parametrize("datos, esperado", [
    pytest.param({}, "", id="ausente"),
    pytest.param({"retroalimentacion": "  Muy completo.  "}, "Muy completo.", id="con-espacios"),
])
def test_leer_retroalimentacion_valida(datos, esperado):
    """Es opcional y se guarda sin espacios a los lados."""
    assert leer_retroalimentacion(datos) == esperado


@pytest.mark.parametrize("valor", [5, None, ["texto"]])
def test_leer_retroalimentacion_que_no_es_texto(valor):
    """Un número, ``null`` o una lista se rechazan con 400."""
    with pytest.raises(DatoInvalidoError, match="retroalimentacion"):
        leer_retroalimentacion({"retroalimentacion": valor})


def test_calificar_guarda_la_retroalimentacion(reloj_fijo):
    """HU-007 pasa el texto a la evaluación que se guarda, en borrador y al confirmar."""
    evaluacion_repo = Mock(spec=EvaluacionRepositorio)
    evaluacion_repo.obtener_asignada.return_value = Evaluacion(
        9, 50, 2, 7, EstadoEvaluacion.PENDIENTE)
    evaluacion_repo.guardar_calificacion.side_effect = lambda evaluacion: evaluacion
    rubrica_repo = Mock(spec=RubricaRepositorio)
    rubrica_repo.obtener_por_feria.return_value = Rubrica(
        4, 7, 1.0, 5.0, (Criterio(1, "Global", 1.0),))
    servicio = CalificacionServicio(evaluacion_repo, rubrica_repo, reloj_fijo(date(2026, 10, 9)))
    for confirmar in (False, True):
        evaluacion = servicio.calificar(50, {"evaluador_id": 2, "notas": {"1": 4.0},
                                             "confirmar": confirmar,
                                             "retroalimentacion": " Bien sustentado. "})
        assert evaluacion.retroalimentacion == "Bien sustentado."
