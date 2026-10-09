"""Comando ``flask init-db``, configuración por defecto y fallas inesperadas de SQLite."""

import sqlite3

import pytest

from app import create_app
from app.db import cerrar_conexion, obtener_conexion
from app.dominio.errores import ErrorPersistencia
from app.dominio.modelos import Rol, Usuario
from app.repositorios.sqlite_repositorios import (
    SqliteAsignaturaRepositorio,
    SqliteUsuarioRepositorio,
)


def test_comando_init_db_con_datos_de_demostracion(tmp_path):
    """``flask init-db --demo`` crea las tablas y carga la feria de ejemplo."""
    ruta = str(tmp_path / "cli.sqlite3")
    app = create_app({"TESTING": True, "DATABASE": ruta})
    resultado = app.test_cli_runner().invoke(args=["init-db", "--demo"])
    assert "datos de demostración" in resultado.output
    conexion = sqlite3.connect(ruta)
    assert conexion.execute("SELECT COUNT(*) FROM feria").fetchone()[0] == 1
    conexion.close()


def test_comando_init_db_sin_demo_deja_tablas_vacias(tmp_path):
    """Sin ``--demo`` solo se crean las tablas."""
    ruta = str(tmp_path / "vacia.sqlite3")
    app = create_app({"TESTING": True, "DATABASE": ruta})
    resultado = app.test_cli_runner().invoke(args=["init-db"])
    assert resultado.output.strip() == "Base de datos inicializada."


def test_configuracion_por_defecto_usa_la_carpeta_instance():
    """Sin configuración, la base va en ``instance/pdep.sqlite3``."""
    assert create_app().config["DATABASE"].endswith("pdep.sqlite3")


def test_falla_de_sqlite_se_traduce_a_error_de_persistencia(conexion):
    """Con la conexión cerrada, ``sqlite3.ProgrammingError`` termina en un 500 controlado."""
    repo = SqliteUsuarioRepositorio(conexion)
    conexion.close()
    with pytest.raises(ErrorPersistencia):
        repo.guardar(Usuario(None, "Ana", "ana@pascualbravo.edu.co", Rol.DOCENTE, 1))


def test_ids_existentes_con_lista_vacia_no_consulta(conexion):
    """Sin asignaturas no se ejecuta ``IN ()``, que sería SQL inválido."""
    assert SqliteAsignaturaRepositorio(conexion).ids_existentes(()) == frozenset()


def test_la_conexion_se_reutiliza_dentro_de_la_misma_solicitud(app):
    """``obtener_conexion`` abre una sola conexión por contexto y ``cerrar_conexion`` tolera
    que no haya ninguna abierta."""
    with app.app_context():
        assert obtener_conexion() is obtener_conexion()
        cerrar_conexion()
        cerrar_conexion()
