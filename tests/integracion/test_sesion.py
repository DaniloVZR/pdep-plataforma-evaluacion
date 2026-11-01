"""RNF-03 · ``POST /api/login`` contra la base temporal con las cuentas de prueba.

Cuentas de app/datos_demo.sql: administrador sin usuario, evaluador = docente 1 y
estudiante = usuario 2 (integrante del Equipo Demo).
"""

import sqlite3

import pytest

from app.repositorios.sqlite_repositorios import SqliteCuentaRepositorio


@pytest.mark.parametrize("correo, clave, esperado", [
    pytest.param("admin@pascualbravo.edu.co", "admin123",
                 {"usuario_id": None, "nombre": "Administración", "rol": "ADMINISTRADOR"},
                 id="administrador"),
    pytest.param("evaluador@pascualbravo.edu.co", "evaluador123",
                 {"usuario_id": 1, "nombre": "Docente Evaluador", "rol": "EVALUADOR"},
                 id="evaluador"),
    pytest.param("estudiante@pascualbravo.edu.co", "estudiante123",
                 {"usuario_id": 2, "nombre": "Estudiante Demo", "rol": "ESTUDIANTE"},
                 id="estudiante"),
])
def test_cada_cuenta_de_prueba_entra_con_su_rol(cliente, correo, clave, esperado):
    """200 con el usuario, el nombre, el rol y el token que necesita la sesión del frontend."""
    respuesta = cliente.post("/api/login", json={"correo": correo, "clave": clave})
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_json()
    token = cuerpo.pop("token")
    assert isinstance(token, str) and token
    assert cuerpo == esperado


def test_clave_incorrecta_responde_401(cliente):
    """Mismo código y mensaje si el correo no existe o la clave no coincide."""
    mala = cliente.post("/api/login", json={"correo": "admin@pascualbravo.edu.co", "clave": "x"})
    inexistente = cliente.post("/api/login",
                               json={"correo": "nadie@pascualbravo.edu.co", "clave": "x"})
    assert mala.status_code == inexistente.status_code == 401
    assert mala.get_json() == inexistente.get_json()
    assert mala.get_json()["codigo"] == "credenciales_invalidas"


def test_cuerpo_que_no_es_json_responde_400(cliente):
    """``get_json(silent=True)`` devuelve None y el validador responde 400."""
    respuesta = cliente.post("/api/login", data="hola", content_type="text/plain")
    assert respuesta.status_code == 400
    assert respuesta.get_json()["codigo"] == "dato_invalido"


def test_repositorio_devuelve_none_si_no_hay_cuenta(conexion):
    """Un correo sin cuenta no es un error del repositorio: lo decide el servicio."""
    assert SqliteCuentaRepositorio(conexion).buscar_por_correo("nadie@pascualbravo.edu.co") is None


@pytest.mark.parametrize("rol, usuario_id", [
    pytest.param("ADMINISTRADOR", 1, id="administrador-con-usuario"),
    pytest.param("ESTUDIANTE", None, id="estudiante-sin-usuario"),
    pytest.param("COORDINADOR", None, id="rol-inexistente"),
])
def test_la_tabla_rechaza_cuentas_inconsistentes(conexion, rol, usuario_id):
    """Solo el administrador va sin usuario y solo existen los tres roles del RTF1."""
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute("INSERT INTO cuenta (correo, clave, rol, usuario_id) VALUES (?, ?, ?, ?)",
                         ("otra@pascualbravo.edu.co", "x", rol, usuario_id))
