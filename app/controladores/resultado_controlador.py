"""Endpoint de HU-009: ``GET /api/resultados?estudiante_id=``."""

from flask import Blueprint, jsonify, request

from app.db import obtener_conexion
from app.dominio.modelos import ResultadoProyecto, RolCuenta
from app.repositorios.sqlite_repositorios import SqliteResultadoRepositorio
from app.servicios.resultado_servicio import ConsultaResultadosServicio
from app.seguridad import exigir_mismo_usuario, requiere_rol

resultados_bp = Blueprint("resultados", __name__, url_prefix="/api")


def construir_servicio() -> ConsultaResultadosServicio:
    """Arma el servicio con el repositorio de SQLite de la solicitud actual."""
    return ConsultaResultadosServicio(SqliteResultadoRepositorio(obtener_conexion()))


def _como_json(proyecto: ResultadoProyecto) -> dict:
    """El proyecto con sus evaluaciones; la fecha de confirmación va en ISO 8601 (RNF-06)."""
    return {
        "proyecto_id": proyecto.proyecto_id,
        "proyecto": proyecto.proyecto,
        "feria": proyecto.feria,
        "equipo": proyecto.equipo,
        "evaluaciones": [{
            "evaluacion_id": evaluacion.evaluacion_id,
            "evaluador": evaluacion.evaluador,
            "estado": evaluacion.estado.value,
            "puntaje_final": evaluacion.puntaje_final,
            "retroalimentacion": evaluacion.retroalimentacion,
            "fecha_confirmacion": (evaluacion.fecha_confirmacion.isoformat()
                                   if evaluacion.fecha_confirmacion else None),
        } for evaluacion in proyecto.evaluaciones],
    }


@resultados_bp.get("/resultados")
@requiere_rol(RolCuenta.ESTUDIANTE)
def consultar_resultados():
    """REQ-17 · Proyectos del estudiante; puntaje y retroalimentación solo si está confirmada.

    ``type=int`` deja ``None`` si el parámetro falta o no es un número; el servicio lo
    rechaza con 400.
    """
    estudiante_id = request.args.get("estudiante_id", type=int)
    exigir_mismo_usuario(estudiante_id)
    proyectos = construir_servicio().consultar(estudiante_id)
    return jsonify([_como_json(proyecto) for proyecto in proyectos])
