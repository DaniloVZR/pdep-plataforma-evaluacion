"""HU-001 · Caminos de ``EstructuraAcademicaServicio``.

El repositorio es ``Mock(spec=EstructuraRepositorio)``: no hay base de datos. En cada
rechazo se comprueba la excepción y que no se llamó al método que guarda.
"""

from dataclasses import replace
from unittest.mock import Mock

import pytest

from app.dominio.errores import (
    ConflictoUnicidadError,
    DatoInvalidoError,
    DepartamentoDuplicadoError,
    DepartamentoNoEncontradoError,
    EstructuraInconsistenteError,
    FacultadDuplicadaError,
    FacultadNoEncontradaError,
    InstitucionDuplicadaError,
    InstitucionNoEncontradaError,
    ProgramaDuplicadoError,
)
from app.repositorios.contratos import EstructuraRepositorio
from app.servicios.estructura_servicio import EstructuraAcademicaServicio


@pytest.fixture(name="repo")
def fixture_repo():
    """Repositorio simulado configurado para el camino exitoso (todo es de la institución 1)."""
    repo = Mock(spec=EstructuraRepositorio)
    repo.existe_institucion.return_value = True
    repo.institucion_de_facultad.return_value = 1
    repo.institucion_de_departamento.return_value = 1
    for metodo in ("guardar_institucion", "guardar_facultad", "guardar_departamento",
                   "guardar_programa"):
        getattr(repo, metodo).side_effect = lambda entidad: replace(entidad, id=7)
    return repo


@pytest.fixture(name="servicio")
def fixture_servicio(repo):
    """Servicio con el repositorio simulado."""
    return EstructuraAcademicaServicio(repo)


# ───────────── Institución (REQ-1) ─────────────

def test_institucion_sin_nombre_no_se_guarda(servicio, repo):
    """Criterio de aceptación 1: falta el nombre de la institución → 400."""
    with pytest.raises(DatoInvalidoError):
        servicio.registrar_institucion({"nit": "890980153"})
    repo.guardar_institucion.assert_not_called()


def test_institucion_exitosa_normaliza_los_textos(servicio, repo):
    """Nombre sin espacios dobles, correo y dominio en minúsculas."""
    institucion = servicio.registrar_institucion({
        "nombre": "  Instituto   Tecnológico ", "nit": " 800 ",
        "correo_contacto": "INFO@ITM.EDU.CO", "dominio": " ITM.edu.co "})
    assert institucion.id == 7
    assert (institucion.nombre, institucion.nit) == ("Instituto Tecnológico", "800")
    assert (institucion.correo_contacto, institucion.telefono) == ("info@itm.edu.co", "")
    assert institucion.dominio == "itm.edu.co"
    repo.guardar_institucion.assert_called_once()


def test_institucion_con_nit_repetido(servicio, repo):
    """La restricción UNIQUE del NIT se traduce a 409."""
    repo.guardar_institucion.side_effect = ConflictoUnicidadError("UNIQUE")
    with pytest.raises(InstitucionDuplicadaError):
        servicio.registrar_institucion({"nombre": "ITM", "nit": "800"})


# ───────────── Facultad y departamento (REQ-2) ─────────────

def test_facultad_sin_nombre_no_consulta_la_base(servicio, repo):
    """Criterio de aceptación 1: falta el nombre de la facultad → 400."""
    with pytest.raises(DatoInvalidoError, match="facultad"):
        servicio.registrar_facultad({"institucion_id": 1, "nombre": " "})
    repo.existe_institucion.assert_not_called()
    repo.guardar_facultad.assert_not_called()


def test_facultad_de_institucion_inexistente(servicio, repo):
    """404 si la institución no existe."""
    repo.existe_institucion.return_value = False
    with pytest.raises(InstitucionNoEncontradaError):
        servicio.registrar_facultad({"institucion_id": 99, "nombre": "Artes"})
    repo.guardar_facultad.assert_not_called()


def test_facultad_repetida(servicio, repo):
    """409 si la institución ya tiene una facultad con ese nombre."""
    repo.guardar_facultad.side_effect = ConflictoUnicidadError("UNIQUE")
    with pytest.raises(FacultadDuplicadaError):
        servicio.registrar_facultad({"institucion_id": 1, "nombre": "Artes"})


def test_facultad_exitosa(servicio):
    """La facultad vuelve con su id y el nombre limpio."""
    facultad = servicio.registrar_facultad({"institucion_id": 1, "nombre": " Artes  y Diseño"})
    assert (facultad.id, facultad.institucion_id, facultad.nombre) == (7, 1, "Artes y Diseño")


def test_departamento_caminos(servicio, repo):
    """Mismos tres caminos para el departamento: 400, 404, 409 y éxito."""
    with pytest.raises(DatoInvalidoError, match="departamento"):
        servicio.registrar_departamento({"institucion_id": 1})
    assert servicio.registrar_departamento(
        {"institucion_id": 1, "nombre": "Ciencias"}).id == 7
    repo.guardar_departamento.side_effect = ConflictoUnicidadError("UNIQUE")
    with pytest.raises(DepartamentoDuplicadoError):
        servicio.registrar_departamento({"institucion_id": 1, "nombre": "Ciencias"})
    repo.existe_institucion.return_value = False
    with pytest.raises(InstitucionNoEncontradaError):
        servicio.registrar_departamento({"institucion_id": 9, "nombre": "Ciencias"})


# ───────────── Programa (REQ-3) ─────────────

PROGRAMA = {"institucion_id": 1, "codigo": " tds ", "nombre": "Desarrollo  de Software"}


def test_programa_sin_facultad_ni_departamento(servicio, repo):
    """D1: REQ-3 exige una de las dos asociaciones."""
    with pytest.raises(DatoInvalidoError):
        servicio.registrar_programa(PROGRAMA)
    repo.guardar_programa.assert_not_called()


def test_programa_de_institucion_inexistente(servicio, repo):
    """D2: 404 antes de revisar la facultad."""
    repo.existe_institucion.return_value = False
    with pytest.raises(InstitucionNoEncontradaError):
        servicio.registrar_programa({**PROGRAMA, "facultad_id": 1})
    repo.institucion_de_facultad.assert_not_called()


def test_programa_con_facultad_inexistente(servicio, repo):
    """D4: la facultad no existe."""
    repo.institucion_de_facultad.return_value = None
    with pytest.raises(FacultadNoEncontradaError):
        servicio.registrar_programa({**PROGRAMA, "facultad_id": 99})


def test_programa_con_facultad_de_otra_institucion(servicio, repo):
    """D5: la facultad es de la institución 2 y el programa de la 1 → 422."""
    repo.institucion_de_facultad.return_value = 2
    with pytest.raises(EstructuraInconsistenteError, match="facultad"):
        servicio.registrar_programa({**PROGRAMA, "facultad_id": 5})
    repo.guardar_programa.assert_not_called()


def test_programa_con_departamento_inexistente(servicio, repo):
    """D7: el departamento no existe."""
    repo.institucion_de_departamento.return_value = None
    with pytest.raises(DepartamentoNoEncontradoError):
        servicio.registrar_programa({**PROGRAMA, "departamento_id": 99})


def test_programa_con_departamento_de_otra_institucion(servicio, repo):
    """D8: el departamento es de otra institución → 422."""
    repo.institucion_de_departamento.return_value = 2
    with pytest.raises(EstructuraInconsistenteError, match="departamento"):
        servicio.registrar_programa({**PROGRAMA, "departamento_id": 3})


def test_programa_con_codigo_repetido(servicio, repo):
    """D9: la restricción UNIQUE del código se traduce a 409."""
    repo.guardar_programa.side_effect = ConflictoUnicidadError("UNIQUE")
    with pytest.raises(ProgramaDuplicadoError):
        servicio.registrar_programa({**PROGRAMA, "departamento_id": 1})


def test_programa_exitoso_con_facultad_y_departamento(servicio, repo):
    """Camino que guarda: código en mayúsculas y nombre limpio."""
    programa = servicio.registrar_programa({**PROGRAMA, "facultad_id": 1, "departamento_id": 1})
    assert (programa.id, programa.codigo, programa.nombre) == (7, "TDS", "Desarrollo de Software")
    assert (programa.facultad_id, programa.departamento_id) == (1, 1)
    repo.guardar_programa.assert_called_once()


def test_programa_exitoso_solo_con_departamento(servicio, repo):
    """Sin facultad no se consulta la facultad."""
    programa = servicio.registrar_programa({**PROGRAMA, "departamento_id": 1})
    assert programa.facultad_id is None
    repo.institucion_de_facultad.assert_not_called()
