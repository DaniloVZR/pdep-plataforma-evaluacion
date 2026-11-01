"""Endpoint de HU-004: ``POST /api/ferias``.

El listado (``GET /api/ferias``) y la rúbrica de cada feria están en ``consulta_controlador``.
"""

from flask import Blueprint, jsonify, request

from app.db import obtener_conexion
from app.repositorios.sqlite_repositorios import SqliteCreacionFeriaRepositorio
from app.servicios.feria_servicio import FeriaServicio
from app.dominio.modelos import RolCuenta
from app.seguridad import requiere_rol

ferias_bp = Blueprint("ferias", __name__, url_prefix="/api")


def construir_servicio() -> FeriaServicio:
    """Arma el servicio con el repositorio de SQLite de la solicitud actual."""
    return FeriaServicio(SqliteCreacionFeriaRepositorio(obtener_conexion()))


@ferias_bp.post("/ferias")
@requiere_rol(RolCuenta.ADMINISTRADOR)
def crear_feria():
    """REQ-7 · 201 con la feria creada; su rúbrica se consulta en /api/ferias/<id>/rubrica."""
    feria = construir_servicio().crear(request.get_json(silent=True))
    return jsonify({
        "id": feria.id,
        "nombre": feria.nombre,
        "fecha_inicio": feria.fecha_inicio.isoformat(),
        "fecha_fin": feria.fecha_fin.isoformat(),
        "asignatura_ids": sorted(feria.asignatura_ids),
    }), 201
