"""HU-004 · Caminos de ``FeriaServicio.crear`` y de su validador.

El repositorio es ``Mock(spec=CreacionFeriaRepositorio)``. Datos simulados: la institución 1
existe y sus asignaturas son la 1 y la 2; la 3 es de otra institución.
"""

from datetime import date
from unittest.mock import Mock

import pytest

from app.dominio.errores import (
    AsignaturaNoEncontradaError,
    DatoInvalidoError,
    FechasFeriaInvalidasError,
    InstitucionNoEncontradaError,
    PesosInvalidosError,
)
from app.dominio.modelos import Feria
from app.repositorios.contratos import CreacionFeriaRepositorio
from app.servicios.feria_servicio import FeriaServicio
from app.validadores.feria_validador import leer_fecha, validar_datos_feria

VALIDA = {
    "institucion_id": 1, "nombre": "  Feria   2027-1 ", "fecha_inicio": "2027-03-01",
    "fecha_fin": "2027-03-15", "asignatura_ids": [1, 2],
    "criterios": [{"nombre": "Funcionalidad", "peso": 0.6},
                  {"nombre": "Presentación", "peso": 0.4}],
}


def con(**cambios):
    """Copia de la solicitud válida con algunos campos cambiados."""
    return {**VALIDA, **cambios}


@pytest.fixture(name="repo")
def fixture_repo():
    """Repositorio simulado configurado para el camino exitoso."""
    repo = Mock(spec=CreacionFeriaRepositorio)
    repo.existe_institucion.side_effect = lambda institucion_id: institucion_id == 1
    repo.asignaturas_de_institucion.side_effect = lambda _i, ids: frozenset(ids) & {1, 2}
    repo.guardar_feria.side_effect = lambda _i, feria, _c: Feria(
        7, feria.nombre, feria.fecha_inicio, feria.fecha_fin, feria.asignatura_ids)
    return repo


@pytest.fixture(name="servicio")
def fixture_servicio(repo):
    """Servicio con el repositorio simulado."""
    return FeriaServicio(repo)


@pytest.mark.parametrize("datos", [
    pytest.param(None, id="cuerpo-nulo"),
    pytest.param(con(institucion_id="1"), id="institucion-texto"),
    pytest.param(con(nombre=" "), id="nombre-vacio"),
    pytest.param(con(fecha_inicio="01/03/2027"), id="fecha-otro-formato"),
    pytest.param(con(fecha_fin="2027-02-30"), id="fecha-inexistente"),
    pytest.param(con(fecha_fin=None), id="fecha-nula"),
    pytest.param(con(asignatura_ids=[]), id="sin-asignaturas"),
    pytest.param(con(asignatura_ids=[1, 1]), id="asignatura-repetida"),
    pytest.param(con(criterios=[]), id="sin-criterios"),
    pytest.param(con(criterios="Funcionalidad"), id="criterios-texto"),
    pytest.param(con(criterios=[{"peso": 1}]), id="criterio-sin-nombre"),
    pytest.param(con(criterios=[{"nombre": "A", "peso": 0}]), id="peso-cero"),
    pytest.param(con(criterios=[{"nombre": "A", "peso": True}]), id="peso-booleano"),
    pytest.param(con(criterios=[{"nombre": "A", "peso": float("nan")}]), id="peso-nan"),
    pytest.param(con(criterios=[{"nombre": "Diseño", "peso": 0.5},
                                {"nombre": " diseño ", "peso": 0.5}]), id="criterio-repetido"),
])
def test_c1_solicitud_mal_formada_no_consulta_la_base(servicio, repo, datos):
    """D1 [no]: cada condición del validador lanza ``DatoInvalidoError`` sin tocar la base."""
    with pytest.raises(DatoInvalidoError):
        servicio.crear(datos)
    repo.existe_institucion.assert_not_called()


@pytest.mark.parametrize("fin", [
    pytest.param("2027-03-01", id="fin-igual-al-inicio"),
    pytest.param("2027-02-28", id="fin-antes-del-inicio"),
])
def test_c2_fin_no_posterior_al_inicio(servicio, repo, fin):
    """D2 [sí]: criterio del RT2, la fecha de fin debe ser posterior a la de inicio."""
    with pytest.raises(FechasFeriaInvalidasError):
        servicio.crear(con(fecha_fin=fin))
    repo.existe_institucion.assert_not_called()


def test_c3_institucion_inexistente(servicio):
    """D3 [no]: la institución 9 no existe."""
    with pytest.raises(InstitucionNoEncontradaError):
        servicio.crear(con(institucion_id=9))


def test_c4_asignatura_de_otra_institucion(servicio, repo):
    """D4 [sí]: la asignatura 3 no es de la institución 1; no se guarda nada."""
    with pytest.raises(AsignaturaNoEncontradaError, match=r"\[3\]"):
        servicio.crear(con(asignatura_ids=[1, 3]))
    repo.guardar_feria.assert_not_called()


@pytest.mark.parametrize("pesos", [
    pytest.param((0.5, 0.3), id="suman-0.8"),
    pytest.param((0.7, 0.7), id="suman-1.4"),
])
def test_c5_pesos_que_no_suman_uno(servicio, repo, pesos):
    """D5 [no]: misma regla de pesos que la rúbrica de HU-007."""
    criterios = [{"nombre": f"C{i}", "peso": p} for i, p in enumerate(pesos)]
    with pytest.raises(PesosInvalidosError):
        servicio.crear(con(criterios=criterios))
    repo.guardar_feria.assert_not_called()


def test_c6_feria_creada_con_datos_limpios(servicio, repo):
    """D5 [sí]: guarda nombre y criterios sin espacios sobrantes, y fechas como ``date``."""
    feria = servicio.crear(con(criterios=[{"nombre": " Funcionalidad ", "peso": 0.6},
                                          {"nombre": "Presentación", "peso": 0.4}]))
    assert (feria.id, feria.nombre) == (7, "Feria 2027-1")
    assert (feria.fecha_inicio, feria.fecha_fin) == (date(2027, 3, 1), date(2027, 3, 15))
    institucion_id, guardada, criterios = repo.guardar_feria.call_args.args
    assert institucion_id == 1 and guardada.asignatura_ids == frozenset({1, 2})
    assert criterios == (("Funcionalidad", 0.6), ("Presentación", 0.4))


def test_pesos_enteros_dentro_de_la_tolerancia(servicio):
    """Un solo criterio con peso 1 (entero) es válido; 0.1 + 0.2 + 0.7 también."""
    servicio.crear(con(criterios=[{"nombre": "Único", "peso": 1}]))
    servicio.crear(con(criterios=[{"nombre": n, "peso": p}
                                  for n, p in (("A", 0.1), ("B", 0.2), ("C", 0.7))]))


def test_leer_fecha_y_validador_con_datos_validos():
    """Formato AAAA-MM-DD con espacios alrededor; otros tipos no son fecha."""
    assert leer_fecha(" 2027-03-01 ") == date(2027, 3, 1)
    assert leer_fecha(20270301) is None
    validar_datos_feria(VALIDA)
