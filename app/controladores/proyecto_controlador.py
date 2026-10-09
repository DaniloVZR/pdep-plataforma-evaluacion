"""Endpoint de HU-005: ``POST /api/proyectos``."""

from flask import Blueprint, jsonify, request

from app.db import obtener_conexion
from app.repositorios.sqlite_repositorios import (
    SqliteEquipoRepositorio,
    SqliteFeriaRepositorio,
    SqliteProyectoRepositorio,
)
from app.servicios.inscripcion_servicio import InscripcionServicio
from app.servicios.reloj import RelojSistema

proyectos_bp = Blueprint("proyectos", __name__, url_prefix="/api/proyectos")


def construir_servicio() -> InscripcionServicio:
    """Arma el servicio con los repositorios de SQLite y el reloj del sistema."""
    conexion = obtener_conexion()
    return InscripcionServicio(
        equipo_repo=SqliteEquipoRepositorio(conexion),
        feria_repo=SqliteFeriaRepositorio(conexion),
        proyecto_repo=SqliteProyectoRepositorio(conexion),
        reloj=RelojSistema(),
    )


@proyectos_bp.post("")
def inscribir_proyecto():
    """Recibe el JSON, delega en el servicio y responde 201 con el proyecto inscrito."""
    proyecto = construir_servicio().inscribir(request.get_json(silent=True))
    return jsonify({
        "id": proyecto.id,
        "equipo_id": proyecto.equipo_id,
        "feria_id": proyecto.feria_id,
        "nombre": proyecto.nombre,
        "modalidad": proyecto.modalidad.value,
        "asignatura_ids": list(proyecto.asignatura_ids),
        "fecha_inscripcion": proyecto.fecha_inscripcion.isoformat(),
    }), 201
