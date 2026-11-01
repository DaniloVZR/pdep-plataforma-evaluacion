"""RNF-03 · Caminos de ``SesionServicio.iniciar_sesion`` y de su validador.

El repositorio es ``Mock(spec=CuentaRepositorio)``. Solo existe la cuenta del
evaluador ``evaluador@pascualbravo.edu.co`` con la clave ``evaluador123``.
"""

from unittest.mock import Mock

import pytest

from app.dominio.errores import CredencialesInvalidasError, DatoInvalidoError
from app.dominio.modelos import Cuenta, RolCuenta
from app.repositorios.contratos import CuentaRepositorio
from app.servicios.sesion_servicio import SesionServicio
from app.validadores.sesion_validador import validar_datos_login

CUENTA = Cuenta("evaluador@pascualbravo.edu.co", "evaluador123", RolCuenta.EVALUADOR, 1,
                "Docente Evaluador")
VALIDO = {"correo": "evaluador@pascualbravo.edu.co", "clave": "evaluador123"}


@pytest.fixture(name="repo")
def fixture_repo():
    """Repositorio simulado que solo conoce la cuenta del evaluador."""
    repo = Mock(spec=CuentaRepositorio)
    repo.buscar_por_correo.side_effect = lambda correo: CUENTA if correo == CUENTA.correo else None
    return repo


@pytest.fixture(name="servicio")
def fixture_servicio(repo):
    """Servicio con el repositorio simulado."""
    return SesionServicio(repo)


@pytest.mark.parametrize("datos", [
    pytest.param(None, id="cuerpo-nulo"),
    pytest.param(["correo"], id="cuerpo-lista"),
    pytest.param({"clave": "x"}, id="sin-correo"),
    pytest.param({**VALIDO, "correo": "   "}, id="correo-vacio"),
    pytest.param({**VALIDO, "correo": 123}, id="correo-numero"),
    pytest.param({"correo": VALIDO["correo"]}, id="sin-clave"),
    pytest.param({**VALIDO, "clave": ""}, id="clave-vacia"),
])
def test_c1_datos_invalidos_no_consultan_la_base(servicio, repo, datos):
    """1 → D1 [no]: falta un campo o no es texto; no se busca ninguna cuenta."""
    with pytest.raises(DatoInvalidoError):
        servicio.iniciar_sesion(datos)
    repo.buscar_por_correo.assert_not_called()


def test_c2_correo_sin_cuenta(servicio):
    """D1 [sí] → D2 [sí] por ``cuenta is None``."""
    with pytest.raises(CredencialesInvalidasError):
        servicio.iniciar_sesion({**VALIDO, "correo": "nadie@pascualbravo.edu.co"})


def test_c3_clave_incorrecta_distingue_mayusculas(servicio):
    """D1 [sí] → D2 [sí] por clave distinta; ``Evaluador123`` no es ``evaluador123``."""
    with pytest.raises(CredencialesInvalidasError):
        servicio.iniciar_sesion({**VALIDO, "clave": "Evaluador123"})


def test_c4_inicio_exitoso_normaliza_el_correo(servicio, repo):
    """D1 [sí] → D2 [no]: el correo se busca en minúsculas y sin espacios."""
    cuenta = servicio.iniciar_sesion({**VALIDO, "correo": "  EVALUADOR@PascualBravo.edu.co "})
    assert cuenta == CUENTA
    repo.buscar_por_correo.assert_called_once_with("evaluador@pascualbravo.edu.co")


def test_validador_acepta_datos_completos():
    """Correo y clave de texto pasan sin excepción."""
    validar_datos_login(VALIDO)
