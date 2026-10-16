"""Endpoints de consulta (GET) que usa el frontend para llenar listas (PDEP-35).

Son de solo lectura: no pasan por los servicios de HU-003, HU-005 y HU-007.
Los parámetros inválidos se rechazan con ``DatoInvalidoError`` (400) y los
recursos inexistentes con su error 404, igual que en el resto de la API.
"""

from flask import Blueprint, jsonify, request

from app.db import obtener_conexion
from app.dominio.errores import DatoInvalidoError, FeriaNoEncontradaError, RubricaNoEncontradaError
from app.dominio.modelos import Rol
from app.repositorios.sqlite_consultas import SqliteConsultaRepositorio

consultas_bp = Blueprint("consultas", __name__, url_prefix="/api")


def _repositorio() -> SqliteConsultaRepositorio:
    return SqliteConsultaRepositorio(obtener_conexion())


def _entero_positivo(nombre: str, obligatorio: bool) -> int | None:
    """Lee ``?nombre=`` como entero mayor que cero. Ausente: ``None`` si es opcional."""
    texto = request.args.get(nombre)
    if texto is None and not obligatorio:
        return None
    if texto is None or not texto.isdigit() or int(texto) == 0:
        raise DatoInvalidoError(f"El parámetro '{nombre}' debe ser un entero mayor que 0.")
    return int(texto)


@consultas_bp.get("/programas")
def listar_programas():
    """Programas con sus asignaturas."""
    return jsonify(_repositorio().listar_programas())


@consultas_bp.get("/usuarios")
def listar_usuarios():
    """Usuarios; ``?rol=DOCENTE`` o ``?rol=ESTUDIANTE`` filtra por rol."""
    rol = request.args.get("rol")
    if rol is not None:
        rol = rol.strip().upper()
        if rol not in {r.value for r in Rol}:
            raise DatoInvalidoError("El parámetro 'rol' debe ser ESTUDIANTE o DOCENTE.")
    return jsonify(_repositorio().listar_usuarios(rol))


@consultas_bp.get("/equipos")
def listar_equipos():
    """Equipos con sus integrantes."""
    return jsonify(_repositorio().listar_equipos())


@consultas_bp.get("/ferias")
def listar_ferias():
    """Ferias con fechas y asignaturas participantes."""
    return jsonify(_repositorio().listar_ferias())


@consultas_bp.get("/ferias/<int:feria_id>/rubrica")
def obtener_rubrica(feria_id: int):
    """Escala y criterios de la rúbrica; 404 si la feria no existe, 422 si no tiene rúbrica."""
    repositorio = _repositorio()
    if not repositorio.existe_feria(feria_id):
        raise FeriaNoEncontradaError("La feria indicada no existe.")
    rubrica = repositorio.obtener_rubrica(feria_id)
    if rubrica is None:
        raise RubricaNoEncontradaError("La feria no tiene una rúbrica asociada.")
    return jsonify(rubrica)


@consultas_bp.get("/proyectos")
def listar_proyectos():
    """Proyectos inscritos; ``?feria_id=1`` filtra por feria."""
    return jsonify(_repositorio().listar_proyectos(_entero_positivo("feria_id", False)))


@consultas_bp.get("/evaluaciones")
def listar_evaluaciones():
    """Evaluaciones asignadas a ``?evaluador_id=`` (obligatorio)."""
    return jsonify(_repositorio().listar_evaluaciones(_entero_positivo("evaluador_id", True)))
