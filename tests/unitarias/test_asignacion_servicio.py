"""HU-006 · Caminos de ``AsignacionServicio.asignar`` y de su validador.

El repositorio es ``Mock(spec=AsignacionRepositorio)``. Datos simulados: el proyecto 1
existe, los usuarios 1 y 3 son docentes y el 2 es estudiante; nadie está asignado todavía.
"""

from unittest.mock import Mock

import pytest

from app.dominio.errores import (
    ConflictoUnicidadError,
    DatoInvalidoError,
    EvaluadorNoEncontradoError,
    EvaluadorYaAsignadoError,
    ProyectoNoEncontradoError,
    UsuarioNoDocenteError,
)
from app.dominio.modelos import Asignacion
from app.repositorios.contratos import AsignacionRepositorio
from app.servicios.asignacion_servicio import AsignacionServicio
from app.validadores.asignacion_validador import validar_datos_asignacion

ROLES = {1: "DOCENTE", 2: "ESTUDIANTE", 3: "DOCENTE"}


@pytest.fixture(name="repo")
def fixture_repo():
    """Repositorio simulado configurado para el camino exitoso."""
    repo = Mock(spec=AsignacionRepositorio)
    repo.existe_proyecto.return_value = True
    repo.roles_de_usuarios.side_effect = lambda ids: {i: ROLES[i] for i in ids if i in ROLES}
    repo.evaluadores_asignados.return_value = frozenset()
    repo.asignar.side_effect = lambda proyecto_id, ids: tuple(
        Asignacion(10 + n, proyecto_id, i) for n, i in enumerate(ids))
    return repo


@pytest.fixture(name="servicio")
def fixture_servicio(repo):
    """Servicio con el repositorio simulado."""
    return AsignacionServicio(repo)


@pytest.mark.parametrize("datos, mensaje", [
    pytest.param(None, "objeto JSON", id="cuerpo-nulo"),
    pytest.param({}, "lista no vacía", id="sin-evaluadores"),
    pytest.param({"evaluador_ids": []}, "lista no vacía", id="lista-vacia"),
    pytest.param({"evaluador_ids": 1}, "lista no vacía", id="no-es-lista"),
    pytest.param({"evaluador_ids": [1, True]}, "lista no vacía", id="booleano"),
    pytest.param({"evaluador_ids": [1, 1]}, "repetidos", id="repetido-en-la-solicitud"),
])
def test_validador_rechaza(datos, mensaje):
    """D1: cada condición del validador."""
    with pytest.raises(DatoInvalidoError, match=mensaje):
        validar_datos_asignacion(datos)


def test_c1_datos_invalidos_no_consultan_la_base(servicio, repo):
    """C1: falla en D1."""
    with pytest.raises(DatoInvalidoError):
        servicio.asignar(1, {"evaluador_ids": [1, 1]})
    repo.existe_proyecto.assert_not_called()


def test_c2_proyecto_inexistente(servicio, repo):
    """C2: D2, el proyecto 99 no existe."""
    repo.existe_proyecto.return_value = False
    with pytest.raises(ProyectoNoEncontradoError):
        servicio.asignar(99, {"evaluador_ids": [1]})
    repo.roles_de_usuarios.assert_not_called()


def test_c3_evaluador_inexistente(servicio, repo):
    """C3: D3, el usuario 99 no existe; el mensaje lo nombra."""
    with pytest.raises(EvaluadorNoEncontradoError, match="99"):
        servicio.asignar(1, {"evaluador_ids": [1, 99]})
    repo.asignar.assert_not_called()


def test_c4_estudiante_no_puede_evaluar(servicio, repo):
    """C4: D4, el usuario 2 es estudiante."""
    with pytest.raises(UsuarioNoDocenteError, match=r"\[2\]"):
        servicio.asignar(1, {"evaluador_ids": [1, 2]})
    repo.asignar.assert_not_called()


def test_c5_evaluador_ya_asignado(servicio, repo):
    """C5: D5, REQ-12. El docente 1 ya tiene el proyecto: no se asigna ninguno."""
    repo.evaluadores_asignados.return_value = frozenset({1})
    with pytest.raises(EvaluadorYaAsignadoError, match=r"\[1\]"):
        servicio.asignar(1, {"evaluador_ids": [3, 1]})
    repo.asignar.assert_not_called()


def test_c6_conflicto_de_unicidad_al_guardar(servicio, repo):
    """C6: D6. Dos solicitudes simultáneas: la restricción UNIQUE es la segunda barrera."""
    repo.asignar.side_effect = ConflictoUnicidadError("UNIQUE constraint failed")
    with pytest.raises(EvaluadorYaAsignadoError):
        servicio.asignar(1, {"evaluador_ids": [1]})


def test_c7_asignacion_de_varios_evaluadores(servicio, repo):
    """C7: REQ-11, se asignan dos docentes en el orden recibido."""
    asignaciones = servicio.asignar(1, {"evaluador_ids": [3, 1]})
    assert [a.evaluador_id for a in asignaciones] == [3, 1]
    repo.asignar.assert_called_once_with(1, (3, 1))
