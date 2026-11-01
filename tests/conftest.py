"""Fixtures compartidas.

- ``reloj_fijo``: reloj con fecha controlada para recorrer los límites del plazo.
- ``app`` y ``cliente``: aplicación Flask sobre una base SQLite temporal
  (``tmp_path``), creada y borrada por cada prueba. Nunca se toca la base real.
"""

from datetime import date, datetime
from unittest.mock import Mock

import pytest

from app import create_app
from app.db import abrir_conexion, ejecutar_script
from app.servicios.reloj import ZONA_HORARIA, Reloj


@pytest.fixture(name="reloj_fijo")
def fixture_reloj_fijo():
    """Fábrica de relojes falsos: ``reloj_fijo(date(2026, 10, 9))``."""
    def crear(dia: date) -> Mock:
        reloj = Mock(spec=Reloj)
        reloj.hoy.return_value = dia
        reloj.ahora.return_value = datetime(dia.year, dia.month, dia.day, 10, 30,
                                            tzinfo=ZONA_HORARIA)
        return reloj
    return crear


@pytest.fixture(name="ruta_bd")
def fixture_ruta_bd(tmp_path):
    """Base SQLite temporal con el esquema y los datos de demostración."""
    ruta = str(tmp_path / "pruebas.sqlite3")
    conexion = abrir_conexion(ruta)
    ejecutar_script(conexion, "schema.sql")
    ejecutar_script(conexion, "datos_demo.sql")
    conexion.close()
    return ruta


@pytest.fixture(name="conexion")
def fixture_conexion(ruta_bd):
    """Conexión directa a la base temporal, para las pruebas de repositorios."""
    conexion = abrir_conexion(ruta_bd)
    yield conexion
    conexion.close()


@pytest.fixture(name="app")
def fixture_app(ruta_bd):
    """Aplicación Flask en modo de pruebas apuntando a la base temporal."""
    return create_app({"TESTING": True, "DATABASE": ruta_bd})


CUENTAS_DE_PRUEBA = {
    "ADMINISTRADOR": ("admin@pascualbravo.edu.co", "admin123"),
    "EVALUADOR": ("evaluador@pascualbravo.edu.co", "evaluador123"),
    "ESTUDIANTE": ("estudiante@pascualbravo.edu.co", "estudiante123"),
}


def _cliente_con_sesion(app, rol: str):
    """Inicia sesión con la cuenta de prueba del rol y deja el token en cada petición."""
    cliente = app.test_client()
    correo, clave = CUENTAS_DE_PRUEBA[rol]
    token = cliente.post("/api/login", json={"correo": correo, "clave": clave}).get_json()["token"]
    cliente.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return cliente


@pytest.fixture(name="cliente")
def fixture_cliente(app):
    """Cliente HTTP de pruebas con sesión de administrador (no abre ningún puerto).

    Desde PDEP-47 la API pide un token. El administrador puede usar todos los
    endpoints, así que las pruebas de cada historia siguen probando sus reglas sin
    cambiar. El control por rol se prueba aparte en ``test_roles.py``.
    """
    return _cliente_con_sesion(app, "ADMINISTRADOR")


@pytest.fixture(name="cliente_como")
def fixture_cliente_como(app):
    """Fábrica de clientes: ``cliente_como("ESTUDIANTE")``; ``None`` = sin sesión."""
    def crear(rol: str | None):
        return app.test_client() if rol is None else _cliente_con_sesion(app, rol)
    return crear
