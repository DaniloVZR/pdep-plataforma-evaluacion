"""HU-003 · Caminos de ``RegistroUsuarioServicio.registrar``. V(G) = 7.

Los repositorios son ``Mock(spec=...)``: no hay base de datos. En cada
rechazo se comprueba la excepción y que ``guardar`` no se llamó.
"""

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.dominio.errores import (
    AsignaturaNoEncontradaError,
    ConflictoUnicidadError,
    CorreoDuplicadoError,
    CorreoNoInstitucionalError,
    DatoInvalidoError,
    ProgramaNoEncontradoError,
)
from app.dominio.modelos import Rol
from app.repositorios.contratos import (
    AsignaturaRepositorio,
    InstitucionRepositorio,
    ProgramaRepositorio,
    UsuarioRepositorio,
)
from app.servicios.registro_usuario_servicio import RegistroUsuarioServicio


@pytest.fixture(name="repos")
def fixture_repos():
    """Repositorios simulados configurados para el camino exitoso."""
    usuario_repo = Mock(spec=UsuarioRepositorio)
    usuario_repo.existe_correo.return_value = False
    usuario_repo.guardar.side_effect = lambda usuario: replace(usuario, id=10)
    institucion_repo = Mock(spec=InstitucionRepositorio)
    institucion_repo.listar_dominios.return_value = frozenset({"pascualbravo.edu.co"})
    programa_repo = Mock(spec=ProgramaRepositorio)
    programa_repo.existe.return_value = True
    asignatura_repo = Mock(spec=AsignaturaRepositorio)
    asignatura_repo.ids_existentes.side_effect = frozenset
    return SimpleNamespace(usuario=usuario_repo, institucion=institucion_repo,
                           programa=programa_repo, asignatura=asignatura_repo)


@pytest.fixture(name="servicio")
def fixture_servicio(repos):
    """Servicio con los repositorios simulados inyectados por el constructor."""
    return RegistroUsuarioServicio(repos.institucion, repos.programa,
                                   repos.asignatura, repos.usuario)


@pytest.fixture(name="datos")
def fixture_datos():
    """Solicitud válida."""
    return {"nombres": "Ana Gómez", "correo": "ana@pascualbravo.edu.co",
            "rol": "ESTUDIANTE", "programa_id": 1, "asignatura_ids": [1, 2]}


def test_c1_datos_invalidos(servicio, repos, datos):
    """C1: 1→2→3→18→19. ``correo = None`` falla en D1."""
    datos["correo"] = None
    with pytest.raises(DatoInvalidoError):
        servicio.registrar(datos)
    repos.institucion.listar_dominios.assert_not_called()
    repos.usuario.guardar.assert_not_called()


def test_c2_correo_no_institucional(servicio, repos, datos):
    """C2: 1→2→4→5→6→18→19. Dominio de un proveedor personal."""
    datos["correo"] = "ana@gmail.com"
    with pytest.raises(CorreoNoInstitucionalError):
        servicio.registrar(datos)
    repos.usuario.existe_correo.assert_not_called()
    repos.usuario.guardar.assert_not_called()


def test_c3_correo_duplicado(servicio, repos, datos):
    """C3: 1→2→4→5→7→8→18→19. El correo ya existe."""
    repos.usuario.existe_correo.return_value = True
    with pytest.raises(CorreoDuplicadoError):
        servicio.registrar(datos)
    repos.usuario.guardar.assert_not_called()


def test_c4_programa_inexistente(servicio, repos, datos):
    """C4: 1→2→4→5→7→9→10→18→19."""
    repos.programa.existe.return_value = False
    with pytest.raises(ProgramaNoEncontradoError):
        servicio.registrar(datos)
    repos.usuario.guardar.assert_not_called()


def test_c5_asignatura_inexistente(servicio, repos, datos):
    """C5: 1→2→4→5→7→9→11→12→13→18→19. La asignatura 99 no existe."""
    datos["asignatura_ids"] = [1, 99]
    repos.asignatura.ids_existentes.side_effect = None
    repos.asignatura.ids_existentes.return_value = frozenset({1})
    with pytest.raises(AsignaturaNoEncontradaError, match="99"):
        servicio.registrar(datos)
    repos.usuario.guardar.assert_not_called()


def test_c6_conflicto_de_unicidad_al_guardar(servicio, repos, datos):
    """C6: 1→2→4→5→7→9→11→12→14→15→16→18→19.

    Simula dos solicitudes simultáneas: ``existe_correo`` dijo que no, pero la
    restricción UNIQUE de la base de datos rechaza el INSERT.
    """
    repos.usuario.guardar.side_effect = ConflictoUnicidadError("UNIQUE constraint failed")
    with pytest.raises(CorreoDuplicadoError):
        servicio.registrar(datos)


def test_c7_registro_exitoso_normaliza_correo_y_rol(servicio, repos, datos):
    """C7: 1→2→4→5→7→9→11→12→14→15→17→19. Único camino que guarda."""
    datos["correo"] = "  Ana@PascualBravo.EDU.CO "
    datos["rol"] = "estudiante"
    datos["asignatura_ids"] = [2, 1, 2]
    usuario = servicio.registrar(datos)
    assert usuario.id == 10
    assert usuario.correo == "ana@pascualbravo.edu.co"
    assert usuario.rol is Rol.ESTUDIANTE
    assert usuario.asignatura_ids == (2, 1)
    repos.usuario.existe_correo.assert_called_once_with("ana@pascualbravo.edu.co")
    repos.usuario.guardar.assert_called_once()


def test_registro_sin_asignaturas_es_valido(servicio, repos, datos):
    """``asignatura_ids`` es opcional: lista vacía no genera faltantes."""
    del datos["asignatura_ids"]
    usuario = servicio.registrar(datos)
    assert usuario.asignatura_ids == ()
    repos.asignatura.ids_existentes.assert_called_once_with(())
