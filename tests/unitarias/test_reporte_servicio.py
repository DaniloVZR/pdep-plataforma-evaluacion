"""HU-010 · Caminos de ``ReporteServicio.generar``, del validador de filtros y de la
consolidación del puntaje.

El repositorio es ``Mock(spec=ReporteRepositorio)``: no hay base de datos.
"""

from unittest.mock import Mock

import pytest

from app.dominio.errores import (
    AsignaturaNoEncontradaError,
    DatoInvalidoError,
    FeriaNoEncontradaError,
    ProgramaNoEncontradoError,
)
from app.dominio.modelos import (
    Agrupacion,
    AsignaturaReporte,
    EstadoEvaluacion,
    FiltrosReporte,
    Modalidad,
    ProyectoReporte,
)
from app.repositorios.contratos import ReporteRepositorio
from app.servicios.reporte_servicio import ReporteServicio
from app.validadores.reporte_validador import leer_filtros

CONFIRMADA = EstadoEvaluacion.CONFIRMADA
BORRADOR = EstadoEvaluacion.BORRADOR
PENDIENTE = EstadoEvaluacion.PENDIENTE
IS2 = AsignaturaReporte(1, "Ingeniería de Software II", 1, "Desarrollo de Software")
BD2 = AsignaturaReporte(2, "Bases de Datos II", 1, "Desarrollo de Software")
CIR = AsignaturaReporte(4, "Circuitos", 2, "Ingeniería Eléctrica")


def proyecto(proyecto_id, nombre, asignaturas, evaluaciones, feria_id=1, feria="Feria 2026-2"):
    """Proyecto de prueba; PIA si tiene más de una asignatura."""
    modalidad = Modalidad.PIA if len(asignaturas) > 1 else Modalidad.PA
    return ProyectoReporte(proyecto_id, nombre, "Equipo Demo", modalidad, feria_id, feria,
                           tuple(asignaturas), tuple(evaluaciones))


# Robot (PIA) y Web confirmados; Inventario con un borrador; Sin evaluar sin evaluadores;
# Medidor confirmado en otra feria y otro programa.
ROBOT = proyecto(1, "Robot", [IS2, BD2], [(CONFIRMADA, 4.0), (CONFIRMADA, 3.0)])
WEB = proyecto(2, "Web", [IS2], [(CONFIRMADA, 3.9)])
INVENTARIO = proyecto(3, "Inventario", [BD2], [(CONFIRMADA, 4.5), (BORRADOR, 2.0)])
SIN_EVALUAR = proyecto(4, "Sin evaluar", [BD2], [])
MEDIDOR = proyecto(5, "Medidor", [CIR], [(CONFIRMADA, 4.8)], feria_id=2, feria="Feria 2026-1")


@pytest.fixture(name="repo")
def fixture_repo():
    """Todo existe y el repositorio devuelve los cinco proyectos."""
    repo = Mock(spec=ReporteRepositorio)
    repo.existe_feria.return_value = True
    repo.existe_asignatura.return_value = True
    repo.existe_programa.return_value = True
    repo.proyectos_para_reporte.return_value = (ROBOT, WEB, INVENTARIO, SIN_EVALUAR, MEDIDOR)
    return repo


@pytest.fixture(name="servicio")
def fixture_servicio(repo):
    """Servicio con el repositorio simulado."""
    return ReporteServicio(repo)


def resumen(grupos):
    """``[(nombre del grupo, [(proyecto, puntaje), ...]), ...]`` para comparar fácil."""
    return [(g.nombre, [(p.proyecto, p.puntaje) for p in g.proyectos]) for g in grupos]


# ───────────── Validador de filtros (D1) ─────────────

def test_sin_parametros_agrupa_por_feria_y_no_filtra():
    """Valores por defecto: feria y ningún filtro."""
    assert leer_filtros({}) == FiltrosReporte()


def test_lee_los_tres_filtros_y_la_agrupacion():
    """Se aceptan espacios alrededor y la agrupación en mayúsculas."""
    filtros = leer_filtros({"agrupar_por": " ASIGNATURA ", "feria_id": " 7 ",
                            "asignatura_id": "2", "programa_id": "", })
    assert filtros == FiltrosReporte(Agrupacion.ASIGNATURA, 7, 2, None)


@pytest.mark.parametrize("valor", [
    pytest.param("0", id="cero"),
    pytest.param("-1", id="negativo"),
    pytest.param("1.5", id="decimal"),
    pytest.param("abc", id="texto"),
    pytest.param("²", id="superindice"),
    pytest.param("1" * 19, id="no-cabe-en-sqlite"),
])
def test_id_invalido_responde_400(valor):
    """Un filtro mal escrito no se ignora: 400 con el nombre del parámetro."""
    with pytest.raises(DatoInvalidoError, match="programa_id"):
        leer_filtros({"programa_id": valor})


def test_agrupacion_desconocida_responde_400():
    """Solo feria, asignatura o programa (REQ-19)."""
    with pytest.raises(DatoInvalidoError, match="agrupar_por"):
        leer_filtros({"agrupar_por": "docente"})


# ───────────── Existencia de lo que se filtra (D2 a D4) ─────────────

@pytest.mark.parametrize("parametro, metodo, error", [
    pytest.param("feria_id", "existe_feria", FeriaNoEncontradaError, id="D2-feria"),
    pytest.param("asignatura_id", "existe_asignatura", AsignaturaNoEncontradaError,
                 id="D3-asignatura"),
    pytest.param("programa_id", "existe_programa", ProgramaNoEncontradoError, id="D4-programa"),
])
def test_filtro_que_no_existe_responde_404(servicio, repo, parametro, metodo, error):
    """404 y no se consultan los proyectos."""
    getattr(repo, metodo).return_value = False
    with pytest.raises(error):
        servicio.generar({parametro: "99"})
    getattr(repo, metodo).assert_called_once_with(99)
    repo.proyectos_para_reporte.assert_not_called()


def test_sin_filtros_no_revisa_existencia(servicio, repo):
    """Sin ids no hay nada que buscar: se va directo a los proyectos."""
    servicio.generar({})
    repo.existe_feria.assert_not_called()
    repo.existe_asignatura.assert_not_called()
    repo.existe_programa.assert_not_called()
    repo.proyectos_para_reporte.assert_called_once_with(None, None, None)


def test_los_filtros_llegan_al_repositorio(servicio, repo):
    """El filtrado por feria, asignatura y programa lo hace la consulta (REQ-19)."""
    servicio.generar({"feria_id": "1", "asignatura_id": "2", "programa_id": "1"})
    repo.proyectos_para_reporte.assert_called_once_with(1, 2, 1)


# ───────────── Consolidación (D5 a D7, REQ-18) ─────────────

@pytest.mark.parametrize("evaluaciones, esperado", [
    pytest.param([], None, id="sin-evaluadores"),
    pytest.param([(PENDIENTE, None)], None, id="pendiente"),
    pytest.param([(CONFIRMADA, 4.0), (BORRADOR, 2.0)], None, id="una-en-borrador"),
    pytest.param([(CONFIRMADA, 3.9)], 3.9, id="un-evaluador"),
    pytest.param([(CONFIRMADA, 4.0), (CONFIRMADA, 3.0), (CONFIRMADA, 3.0)], 3.33,
                 id="promedio-redondeado"),
])
def test_puntaje_consolidado(evaluaciones, esperado):
    """Solo con TODAS las evaluaciones confirmadas; promedio con dos decimales."""
    assert proyecto(9, "X", [IS2], evaluaciones).puntaje_consolidado() == esperado


def test_solo_entran_los_proyectos_confirmados(servicio):
    """Criterio de aceptación 1: Inventario y Sin evaluar quedan como pendientes."""
    reporte = servicio.generar({})
    assert (reporte.consolidados, reporte.pendientes) == (3, 2)
    assert reporte.promedio_general == round((3.5 + 3.9 + 4.8) / 3, 2)
    assert resumen(reporte.grupos) == [
        ("Feria 2026-1", [("Medidor", 4.8)]),
        ("Feria 2026-2", [("Web", 3.9), ("Robot", 3.5)]),
    ]


def test_sin_proyectos_confirmados_no_hay_promedio(servicio, repo):
    """D7: sin proyectos consolidados el promedio general es None, no un error."""
    repo.proyectos_para_reporte.return_value = (INVENTARIO, SIN_EVALUAR)
    reporte = servicio.generar({})
    assert (reporte.grupos, reporte.consolidados, reporte.pendientes) == ((), 0, 2)
    assert reporte.promedio_general is None


# ───────────── Agrupación (G1, G2, REQ-19) ─────────────

def test_por_asignatura_el_pia_aparece_en_cada_una(servicio):
    """Robot es PIA de IS2 y BD2: cuenta en las dos asignaturas."""
    reporte = servicio.generar({"agrupar_por": "asignatura"})
    assert resumen(reporte.grupos) == [
        ("Bases de Datos II", [("Robot", 3.5)]),
        ("Circuitos", [("Medidor", 4.8)]),
        ("Ingeniería de Software II", [("Web", 3.9), ("Robot", 3.5)]),
    ]
    assert reporte.consolidados == 3       # los proyectos se cuentan una sola vez


def test_por_programa_el_pia_aparece_una_vez(servicio):
    """Las dos asignaturas de Robot son del mismo programa: aparece una vez."""
    reporte = servicio.generar({"agrupar_por": "programa"})
    assert resumen(reporte.grupos) == [
        ("Desarrollo de Software", [("Web", 3.9), ("Robot", 3.5)]),
        ("Ingeniería Eléctrica", [("Medidor", 4.8)]),
    ]


def test_estadisticas_del_grupo_y_empates(servicio, repo):
    """Promedio, máximo y mínimo; con el mismo puntaje se ordena por nombre."""
    repo.proyectos_para_reporte.return_value = (
        proyecto(1, "Zeta", [IS2], [(CONFIRMADA, 4.0)]),
        proyecto(2, "Alfa", [IS2], [(CONFIRMADA, 4.0)]),
        proyecto(3, "Beta", [IS2], [(CONFIRMADA, 2.5)]),
    )
    grupo = servicio.generar({}).grupos[0]
    assert [p.proyecto for p in grupo.proyectos] == ["Alfa", "Zeta", "Beta"]
    assert (grupo.promedio, grupo.maximo, grupo.minimo) == (3.5, 4.0, 2.5)
    assert grupo.proyectos[0].evaluaciones == 1
