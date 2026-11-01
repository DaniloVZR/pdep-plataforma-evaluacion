"""HU-002 · Caminos de ``RegistroAsignaturaServicio`` y condiciones de su validador.

Los repositorios son ``Mock(spec=...)``: no hay base de datos. En cada rechazo se
comprueba la excepción y que no se llamó al método que guarda.
"""

from dataclasses import replace
from unittest.mock import Mock

import pytest

from app.dominio.errores import (
    AsignaturaDuplicadaError,
    ConflictoUnicidadError,
    DatoInvalidoError,
    ProgramaNoEncontradoError,
)
from app.repositorios.contratos import ProgramaRepositorio, RegistroAsignaturaRepositorio
from app.servicios.asignatura_servicio import RegistroAsignaturaServicio

ASIGNATURA = {"programa_id": 1, "codigo": "IS3", "nombre": "Ingeniería de Software III",
              "semestre": 6}


def sin(datos, campo):
    """Copia de ``datos`` sin un campo."""
    return {clave: valor for clave, valor in datos.items() if clave != campo}


@pytest.fixture(name="programa_repo")
def fixture_programa_repo():
    """El programa 1 existe."""
    repo = Mock(spec=ProgramaRepositorio)
    repo.existe.return_value = True
    return repo


@pytest.fixture(name="asignatura_repo")
def fixture_asignatura_repo():
    """Guarda la asignatura y le pone el id 9."""
    repo = Mock(spec=RegistroAsignaturaRepositorio)
    repo.guardar.side_effect = lambda asignatura: replace(asignatura, id=9)
    return repo


@pytest.fixture(name="servicio")
def fixture_servicio(programa_repo, asignatura_repo):
    """Servicio con los repositorios simulados."""
    return RegistroAsignaturaServicio(programa_repo, asignatura_repo)


@pytest.mark.parametrize("datos, mensaje", [
    pytest.param(None, "objeto JSON", id="cuerpo-nulo"),
    pytest.param(sin(ASIGNATURA, "programa_id"), "programa académico", id="sin-programa"),
    pytest.param({**ASIGNATURA, "programa_id": True}, "programa académico",
                 id="programa-booleano"),
    pytest.param({**ASIGNATURA, "programa_id": "1"}, "programa académico",
                 id="programa-texto"),
    pytest.param(sin(ASIGNATURA, "codigo"), "código", id="sin-codigo"),
    pytest.param({**ASIGNATURA, "nombre": "   "}, "nombre", id="nombre-vacio"),
    pytest.param(sin(ASIGNATURA, "semestre"), "semestre", id="sin-semestre"),
    pytest.param({**ASIGNATURA, "semestre": 0}, "semestre", id="semestre-cero"),
    pytest.param({**ASIGNATURA, "semestre": 5.5}, "semestre", id="semestre-decimal"),
])
def test_datos_invalidos_no_consultan_la_base(servicio, programa_repo, asignatura_repo,
                                              datos, mensaje):
    """D1 verdadero: 400 antes de consultar el programa."""
    with pytest.raises(DatoInvalidoError, match=mensaje):
        servicio.registrar(datos)
    programa_repo.existe.assert_not_called()
    asignatura_repo.guardar.assert_not_called()


def test_programa_inexistente_responde_404(servicio, programa_repo, asignatura_repo):
    """D2 verdadero: el programa 99 no existe y la asignatura no se guarda."""
    programa_repo.existe.return_value = False
    with pytest.raises(ProgramaNoEncontradoError):
        servicio.registrar({**ASIGNATURA, "programa_id": 99})
    programa_repo.existe.assert_called_once_with(99)
    asignatura_repo.guardar.assert_not_called()


def test_codigo_repetido_responde_409(servicio, asignatura_repo):
    """D3 verdadero: la restricción UNIQUE del código se traduce a 409."""
    asignatura_repo.guardar.side_effect = ConflictoUnicidadError("UNIQUE")
    with pytest.raises(AsignaturaDuplicadaError):
        servicio.registrar(ASIGNATURA)


def test_asignatura_queda_asociada_al_programa_seleccionado(servicio, asignatura_repo):
    """Camino exitoso (criterios 1 y 2): código en mayúsculas y nombre sin espacios dobles."""
    asignatura = servicio.registrar({**ASIGNATURA, "codigo": " is3 ",
                                     "nombre": "  Ingeniería   de Software III "})
    assert asignatura.id == 9
    assert asignatura.programa_id == 1
    assert (asignatura.codigo, asignatura.nombre) == ("IS3", "Ingeniería de Software III")
    assert asignatura.semestre == 6
    asignatura_repo.guardar.assert_called_once()
