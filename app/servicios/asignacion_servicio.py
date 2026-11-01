"""Caso de uso HU-006: asignar uno o varios evaluadores a un proyecto."""

from app.dominio.errores import (
    ConflictoUnicidadError,
    EvaluadorNoEncontradoError,
    EvaluadorYaAsignadoError,
    ProyectoNoEncontradoError,
    UsuarioNoDocenteError,
)
from app.dominio.modelos import Asignacion, Rol
from app.repositorios.contratos import AsignacionRepositorio
from app.validadores.asignacion_validador import validar_datos_asignacion

MENSAJE_YA_ASIGNADO = "El evaluador ya está asignado a este proyecto."


class AsignacionServicio:
    """Coordina las validaciones y la creación de las evaluaciones pendientes."""

    def __init__(self, repositorio: AsignacionRepositorio) -> None:
        self._repo = repositorio

    def asignar(self, proyecto_id: int, datos: object) -> tuple[Asignacion, ...]:
        """Asigna los evaluadores (REQ-11) sin repetir ninguno en el proyecto (REQ-12).

        Si un solo evaluador no cumple, no se asigna ninguno: la solicitud es todo o nada.
        """
        validar_datos_asignacion(datos)                                  # D1
        if not self._repo.existe_proyecto(proyecto_id):                  # D2
            raise ProyectoNoEncontradoError("El proyecto indicado no existe.")
        ids = tuple(datos["evaluador_ids"])
        roles = self._repo.roles_de_usuarios(ids)
        faltantes = sorted(set(ids) - roles.keys())
        if faltantes:                                                    # D3
            raise EvaluadorNoEncontradoError(f"No existen los usuarios {faltantes}.")
        estudiantes = sorted(i for i in ids if roles[i] != Rol.DOCENTE.value)
        if estudiantes:                                                  # D4
            raise UsuarioNoDocenteError(
                f"Solo un docente puede evaluar; {estudiantes} no son docentes.")
        repetidos = sorted(set(ids) & self._repo.evaluadores_asignados(proyecto_id))
        if repetidos:                                                    # D5
            raise EvaluadorYaAsignadoError(
                f"{MENSAJE_YA_ASIGNADO} Evaluadores repetidos: {repetidos}.")
        try:
            return self._repo.asignar(proyecto_id, ids)
        except ConflictoUnicidadError as error:                           # D6
            raise EvaluadorYaAsignadoError(MENSAJE_YA_ASIGNADO) from error
