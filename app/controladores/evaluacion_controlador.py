"""Endpoint de HU-007: ``PUT /api/proyectos/<id>/evaluacion``."""

from flask import Blueprint, jsonify, request

from app.db import obtener_conexion
from app.repositorios.sqlite_repositorios import (
    SqliteEvaluacionRepositorio,
    SqliteRubricaRepositorio,
)
from app.servicios.calificacion_servicio import CalificacionServicio
from app.servicios.reloj import RelojSistema

evaluaciones_bp = Blueprint("evaluaciones", __name__, url_prefix="/api/proyectos")


def construir_servicio() -> CalificacionServicio:
    """Arma el servicio con los repositorios de SQLite y el reloj del sistema."""
    conexion = obtener_conexion()
    return CalificacionServicio(
        evaluacion_repo=SqliteEvaluacionRepositorio(conexion),
        rubrica_repo=SqliteRubricaRepositorio(conexion),
        reloj=RelojSistema(),
    )


@evaluaciones_bp.put("/<int:proyecto_id>/evaluacion")
def calificar_proyecto(proyecto_id: int):
    """Califica el proyecto. El puntaje solo se devuelve si la evaluación quedó confirmada."""
    evaluacion = construir_servicio().calificar(proyecto_id, request.get_json(silent=True))
    fecha = evaluacion.fecha_confirmacion
    return jsonify({
        "evaluacion_id": evaluacion.id,
        "proyecto_id": evaluacion.proyecto_id,
        "estado": evaluacion.estado.value,
        "puntaje_final": evaluacion.puntaje_visible,
        "fecha_confirmacion": fecha.isoformat() if fecha else None,
    }), 200
