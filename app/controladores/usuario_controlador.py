"""Endpoint de HU-003: ``POST /api/usuarios``."""

from flask import Blueprint, jsonify, request

from app.db import obtener_conexion
from app.repositorios.sqlite_repositorios import (
    SqliteAsignaturaRepositorio,
    SqliteInstitucionRepositorio,
    SqliteProgramaRepositorio,
    SqliteUsuarioRepositorio,
)
from app.servicios.registro_usuario_servicio import RegistroUsuarioServicio

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/api/usuarios")


def construir_servicio() -> RegistroUsuarioServicio:
    """Arma el servicio con los repositorios de SQLite de la solicitud actual."""
    conexion = obtener_conexion()
    return RegistroUsuarioServicio(
        institucion_repo=SqliteInstitucionRepositorio(conexion),
        programa_repo=SqliteProgramaRepositorio(conexion),
        asignatura_repo=SqliteAsignaturaRepositorio(conexion),
        usuario_repo=SqliteUsuarioRepositorio(conexion),
    )


@usuarios_bp.post("")
def registrar_usuario():
    """Recibe el JSON, delega en el servicio y responde 201 con el usuario creado.

    Si el servicio lanza un ``ErrorDominio``, lo atrapa el manejador global de
    ``create_app`` y responde con el código HTTP de la excepción.
    """
    usuario = construir_servicio().registrar(request.get_json(silent=True))
    return jsonify({
        "id": usuario.id,
        "nombres": usuario.nombres,
        "correo": usuario.correo,
        "rol": usuario.rol.value,
        "programa_id": usuario.programa_id,
        "asignatura_ids": list(usuario.asignatura_ids),
    }), 201
