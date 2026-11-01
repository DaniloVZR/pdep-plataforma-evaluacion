"""Endpoints de HU-001: registrar institución, facultades, departamentos y programas.

Los listados (GET) están en ``consulta_controlador`` junto a las demás consultas.
"""

from dataclasses import asdict

from flask import Blueprint, jsonify, request

from app.db import obtener_conexion
from app.repositorios.sqlite_repositorios import SqliteEstructuraRepositorio
from app.servicios.estructura_servicio import EstructuraAcademicaServicio
from app.dominio.modelos import RolCuenta
from app.seguridad import requiere_rol

estructura_bp = Blueprint("estructura", __name__, url_prefix="/api")


def construir_servicio() -> EstructuraAcademicaServicio:
    """Arma el servicio con el repositorio de SQLite de la solicitud actual."""
    return EstructuraAcademicaServicio(SqliteEstructuraRepositorio(obtener_conexion()))


@estructura_bp.post("/instituciones")
@requiere_rol(RolCuenta.ADMINISTRADOR)
def registrar_institucion():
    """REQ-1 · 201 con la institución creada."""
    institucion = construir_servicio().registrar_institucion(request.get_json(silent=True))
    return jsonify(asdict(institucion)), 201


@estructura_bp.post("/facultades")
@requiere_rol(RolCuenta.ADMINISTRADOR)
def registrar_facultad():
    """REQ-2 · 201 con la facultad creada."""
    facultad = construir_servicio().registrar_facultad(request.get_json(silent=True))
    return jsonify(asdict(facultad)), 201


@estructura_bp.post("/departamentos")
@requiere_rol(RolCuenta.ADMINISTRADOR)
def registrar_departamento():
    """REQ-2 · 201 con el departamento creado."""
    departamento = construir_servicio().registrar_departamento(request.get_json(silent=True))
    return jsonify(asdict(departamento)), 201


@estructura_bp.post("/programas")
@requiere_rol(RolCuenta.ADMINISTRADOR)
def registrar_programa():
    """REQ-3 · 201 con el programa creado."""
    programa = construir_servicio().registrar_programa(request.get_json(silent=True))
    return jsonify(asdict(programa)), 201
