"""Endpoint de HU-010: ``GET /api/reportes``.

Parámetros opcionales: ``agrupar_por`` (feria, asignatura o programa; por defecto feria),
``feria_id``, ``asignatura_id`` y ``programa_id``.
"""

from flask import Blueprint, jsonify, request

from app.db import obtener_conexion
from app.dominio.modelos import GrupoReporte, Reporte, RolCuenta
from app.repositorios.sqlite_repositorios import SqliteReporteRepositorio
from app.seguridad import requiere_rol
from app.servicios.reporte_servicio import ReporteServicio

reportes_bp = Blueprint("reportes", __name__, url_prefix="/api")


def construir_servicio() -> ReporteServicio:
    """Arma el servicio con el repositorio de SQLite de la solicitud actual."""
    return ReporteServicio(SqliteReporteRepositorio(obtener_conexion()))


def _grupo_como_json(grupo: GrupoReporte) -> dict:
    return {
        "id": grupo.id,
        "nombre": grupo.nombre,
        "cantidad": len(grupo.proyectos),
        "promedio": grupo.promedio,
        "maximo": grupo.maximo,
        "minimo": grupo.minimo,
        "proyectos": [{
            "proyecto_id": p.proyecto_id,
            "proyecto": p.proyecto,
            "equipo": p.equipo,
            "modalidad": p.modalidad.value,
            "feria": p.feria,
            "puntaje": p.puntaje,
            "evaluaciones": p.evaluaciones,
        } for p in grupo.proyectos],
    }


def _como_json(reporte: Reporte) -> dict:
    filtros = reporte.filtros
    return {
        "agrupar_por": filtros.agrupar_por.value,
        "filtros": {"feria_id": filtros.feria_id, "asignatura_id": filtros.asignatura_id,
                    "programa_id": filtros.programa_id},
        "resumen": {"proyectos_consolidados": reporte.consolidados,
                    "proyectos_pendientes": reporte.pendientes,
                    "promedio_general": reporte.promedio_general},
        "grupos": [_grupo_como_json(grupo) for grupo in reporte.grupos],
    }


@reportes_bp.get("/reportes")
@requiere_rol(RolCuenta.ADMINISTRADOR)
def generar_reporte():
    """REQ-18 y REQ-19 · Reporte consolidado, solo con proyectos de evaluación confirmada."""
    return jsonify(_como_json(construir_servicio().generar(request.args)))
