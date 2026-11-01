"""Endpoint de HU-006: ``POST /api/proyectos/<id>/evaluadores``.

La carga de cada evaluador (``GET /api/evaluadores/carga``) está en ``consulta_controlador``.
"""

from flask import Blueprint, jsonify, request

from app.db import obtener_conexion
from app.repositorios.sqlite_repositorios import SqliteAsignacionRepositorio
from app.servicios.asignacion_servicio import AsignacionServicio
from app.dominio.modelos import RolCuenta
from app.seguridad import requiere_rol

asignaciones_bp = Blueprint("asignaciones", __name__, url_prefix="/api/proyectos")


def construir_servicio() -> AsignacionServicio:
    """Arma el servicio con el repositorio de SQLite de la solicitud actual."""
    return AsignacionServicio(SqliteAsignacionRepositorio(obtener_conexion()))


@asignaciones_bp.post("/<int:proyecto_id>/evaluadores")
@requiere_rol(RolCuenta.ADMINISTRADOR)
def asignar_evaluadores(proyecto_id: int):
    """Responde 201 con una evaluación PENDIENTE por cada evaluador asignado."""
    asignaciones = construir_servicio().asignar(proyecto_id, request.get_json(silent=True))
    return jsonify({
        "proyecto_id": proyecto_id,
        "asignados": [{"evaluacion_id": a.evaluacion_id, "evaluador_id": a.evaluador_id}
                      for a in asignaciones],
    }), 201
