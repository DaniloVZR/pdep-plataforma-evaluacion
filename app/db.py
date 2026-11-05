"""Conexión a SQLite por solicitud y comandos para crear la base de datos."""

from importlib import resources
import sqlite3

import click
from flask import Flask, current_app, g
from flask.cli import with_appcontext


def abrir_conexion(ruta: str) -> sqlite3.Connection:
    """Abre una conexión con claves foráneas activas y filas accesibles por nombre."""
    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def obtener_conexion() -> sqlite3.Connection:
    """Devuelve la conexión de la solicitud actual y la crea si no existe."""
    if "conexion" not in g:
        g.conexion = abrir_conexion(current_app.config["DATABASE"])
    return g.conexion


def cerrar_conexion(_error: BaseException | None = None) -> None:
    """Cierra la conexión al terminar la solicitud."""
    conexion = g.pop("conexion", None)
    if conexion is not None:
        conexion.close()


def ejecutar_script(conexion: sqlite3.Connection, nombre: str) -> None:
    """Ejecuta un archivo .sql del paquete ``app``."""
    script = resources.files("app").joinpath(nombre).read_text(encoding="utf-8")
    conexion.executescript(script)


@click.command("init-db")
@click.option("--demo", is_flag=True, help="Carga además los datos de demostración.")
@click.option("--ejemplo", is_flag=True,
              help="Carga los datos de demostración y, encima, varias ferias, equipos, "
                   "proyectos y evaluaciones para probar a mano.")
@with_appcontext
def comando_init_db(demo: bool, ejemplo: bool) -> None:
    """Borra y crea las tablas. Con --demo carga los datos mínimos que usan las pruebas;
    con --ejemplo, además, los datos de ejemplo compartidos (datos_ejemplo.sql)."""
    conexion = obtener_conexion()
    ejecutar_script(conexion, "schema.sql")
    if demo or ejemplo:
        ejecutar_script(conexion, "datos_demo.sql")
    if ejemplo:
        ejecutar_script(conexion, "datos_ejemplo.sql")
        click.echo("Base de datos inicializada con datos de ejemplo.")
    elif demo:
        click.echo("Base de datos inicializada con datos de demostración.")
    else:
        click.echo("Base de datos inicializada.")


def registrar_en(app: Flask) -> None:
    """Conecta el cierre de la conexión y el comando ``flask init-db``."""
    app.teardown_appcontext(cerrar_conexion)
    app.cli.add_command(comando_init_db)
