"""Endpoint del inicio de sesión (RNF-03): ``POST /api/login``."""

from flask import Blueprint, jsonify, request

from app.db import obtener_conexion
from app.repositorios.sqlite_repositorios import SqliteCuentaRepositorio
from app.servicios.sesion_servicio import SesionServicio
from app.seguridad import emitir_token

sesion_bp = Blueprint("sesion", __name__, url_prefix="/api")


def construir_servicio() -> SesionServicio:
    """Arma el servicio con el repositorio de cuentas de la solicitud actual."""
    return SesionServicio(SqliteCuentaRepositorio(obtener_conexion()))


@sesion_bp.post("/login")
def iniciar_sesion():
    """Responde 200 con el usuario, su nombre, su rol y el token; 400 o 401 si no puede entrar.

    El frontend envía el token en cada petición (``Authorization: Bearer``, PDEP-47).
    """
    cuenta = construir_servicio().iniciar_sesion(request.get_json(silent=True))
    return jsonify({
        "usuario_id": cuenta.usuario_id,
        "nombre": cuenta.nombre,
        "rol": cuenta.rol.value,
        "token": emitir_token(cuenta),
    })
