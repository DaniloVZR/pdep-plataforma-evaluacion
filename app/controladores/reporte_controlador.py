"""Endpoints de HU-010: ``GET /api/reportes`` y ``GET /api/reportes/excel``.

Parámetros opcionales: ``agrupar_por`` (feria, asignatura o programa; por defecto feria),
``feria_id``, ``asignatura_id`` y ``programa_id``.
"""

from dataclasses import asdict

from flask import Blueprint, Response, jsonify, request

from app.db import obtener_conexion
from app.dominio.modelos import (
    EvaluacionReporte,
    GrupoReporte,
    ProyectoConsolidado,
    Reporte,
    RolCuenta,
)
from app.repositorios.sqlite_repositorios import SqliteReporteRepositorio
from app.seguridad import requiere_rol
from app.servicios.reloj import RelojSistema
from app.servicios.reporte_excel import TIPO_XLSX, generar_excel, nombre_archivo
from app.servicios.reporte_servicio import ReporteServicio

reportes_bp = Blueprint("reportes", __name__, url_prefix="/api")


def construir_servicio() -> ReporteServicio:
    """Arma el servicio con el repositorio de SQLite y el reloj del sistema."""
    return ReporteServicio(SqliteReporteRepositorio(obtener_conexion()), RelojSistema())


def _evaluacion_como_json(evaluacion: EvaluacionReporte) -> dict:
    fecha = evaluacion.fecha_confirmacion
    return {
        "evaluador": evaluacion.evaluador,
        "estado": evaluacion.estado.value,
        "puntaje_final": evaluacion.puntaje_final,
        "fecha_confirmacion": fecha.isoformat() if fecha else None,
        "retroalimentacion": evaluacion.retroalimentacion,
    }


def _proyecto_como_json(proyecto: ProyectoConsolidado) -> dict:
    return {
        "proyecto_id": proyecto.proyecto_id,
        "proyecto": proyecto.proyecto,
        "equipo": proyecto.equipo,
        "integrantes": list(proyecto.integrantes),
        "modalidad": proyecto.modalidad.value,
        "feria": proyecto.feria,
        "asignaturas": list(proyecto.asignaturas),
        "puntaje": proyecto.puntaje,
        "nivel": proyecto.nivel.value,
        "criterios": [asdict(c) for c in proyecto.criterios],
        "evaluaciones": [_evaluacion_como_json(e) for e in proyecto.evaluaciones],
    }


def _distribucion_como_json(distribucion) -> dict:
    return {**asdict(distribucion), "aprobados": distribucion.aprobados,
            "reprobados": distribucion.reprobados}


def _grupo_como_json(grupo: GrupoReporte) -> dict:
    return {
        "id": grupo.id,
        "nombre": grupo.nombre,
        "cantidad": len(grupo.proyectos),
        "promedio": grupo.promedio,
        "maximo": grupo.maximo,
        "minimo": grupo.minimo,
        "distribucion": _distribucion_como_json(grupo.distribucion),
        "criterios": [asdict(c) for c in grupo.criterios],
        "proyectos": [_proyecto_como_json(p) for p in grupo.proyectos],
    }


def _como_json(reporte: Reporte) -> dict:
    filtros, avance = reporte.filtros, reporte.avance
    return {
        "agrupar_por": filtros.agrupar_por.value,
        "filtros": {"feria_id": filtros.feria_id, "asignatura_id": filtros.asignatura_id,
                    "programa_id": filtros.programa_id},
        "generado": reporte.generado.isoformat(),
        "resumen": {"proyectos_consolidados": reporte.consolidados,
                    "proyectos_pendientes": len(reporte.pendientes),
                    "promedio_general": reporte.promedio_general},
        "distribucion": _distribucion_como_json(reporte.distribucion),
        "avance": {**asdict(avance), "porcentaje": avance.porcentaje},
        "pendientes": [{
            "proyecto_id": p.proyecto_id, "proyecto": p.proyecto, "equipo": p.equipo,
            "feria": p.feria, "confirmadas": p.confirmadas, "total": p.total,
            "faltantes": [_evaluacion_como_json(e) for e in p.faltantes],
        } for p in reporte.pendientes],
        "grupos": [_grupo_como_json(grupo) for grupo in reporte.grupos],
    }


@reportes_bp.get("/reportes")
@requiere_rol(RolCuenta.ADMINISTRADOR)
def generar_reporte():
    """REQ-18 y REQ-19 · Reporte consolidado, solo con proyectos de evaluación confirmada."""
    return jsonify(_como_json(construir_servicio().generar(request.args)))


@reportes_bp.get("/reportes/excel")
@requiere_rol(RolCuenta.ADMINISTRADOR)
def descargar_reporte_excel():
    """El mismo reporte, con los mismos filtros, como archivo de Excel (.xlsx)."""
    reporte = construir_servicio().generar(request.args)
    return Response(generar_excel(reporte), mimetype=TIPO_XLSX, headers={
        "Content-Disposition": f'attachment; filename="{nombre_archivo(reporte)}"'})
