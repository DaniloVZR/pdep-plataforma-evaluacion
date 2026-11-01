"""Endpoint de HU-002: ``POST /api/asignaturas``.

El listado por programa (``GET /api/asignaturas?programa_id=``) está en ``consulta_controlador``.
"""

from dataclasses import asdict

from flask import Blueprint, jsonify, request

from app.db import obtener_conexion
from app.repositorios.sqlite_repositorios import (
    SqliteProgramaRepositorio,
    SqliteRegistroAsignaturaRepositorio,
)
from app.servicios.asignatura_servicio import RegistroAsignaturaServicio

asignaturas_bp = Blueprint("asignaturas", __name__, url_prefix="/api")


def construir_servicio() -> RegistroAsignaturaServicio:
    """Arma el servicio con los repositorios de SQLite de la solicitud actual."""
    conexion = obtener_conexion()
    return RegistroAsignaturaServicio(
        programa_repo=SqliteProgramaRepositorio(conexion),
        asignatura_repo=SqliteRegistroAsignaturaRepositorio(conexion),
    )


@asignaturas_bp.post("/asignaturas")
def registrar_asignatura():
    """REQ-4 · 201 con la asignatura creada y el programa al que quedó asociada."""
    asignatura = construir_servicio().registrar(request.get_json(silent=True))
    return jsonify(asdict(asignatura)), 201
