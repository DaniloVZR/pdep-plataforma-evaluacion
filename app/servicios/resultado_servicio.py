"""Caso de uso HU-009: consultar la calificación y la retroalimentación (REQ-17, RN007)."""

from dataclasses import replace

from app.dominio.errores import (
    DatoInvalidoError,
    UsuarioNoEncontradoError,
    UsuarioNoEstudianteError,
)
from app.dominio.modelos import ResultadoProyecto, Rol
from app.repositorios.contratos import ResultadoRepositorio
from app.validadores.comunes import es_entero_positivo


class ConsultaResultadosServicio:
    """Devuelve los proyectos del estudiante y publica solo las evaluaciones confirmadas."""

    def __init__(self, repositorio: ResultadoRepositorio) -> None:
        self._repo = repositorio

    def consultar(self, estudiante_id: object) -> tuple[ResultadoProyecto, ...]:
        """400 si el id no es válido, 404 si el usuario no existe, 422 si no es estudiante.

        Recorre cada proyecto y cada evaluación: la confirmada se publica completa; las
        demás muestran solo su estado (RN007).
        """
        if not es_entero_positivo(estudiante_id):                          # D1
            raise DatoInvalidoError(
                "El parámetro 'estudiante_id' debe ser un entero mayor que 0.")
        rol = self._repo.rol_de_usuario(estudiante_id)
        if rol is None:                                                    # D2
            raise UsuarioNoEncontradoError("El usuario indicado no existe.")
        if rol != Rol.ESTUDIANTE.value:                                    # D3
            raise UsuarioNoEstudianteError(
                "Solo un estudiante puede consultar los resultados de sus proyectos.")
        return tuple(
            replace(proyecto, evaluaciones=tuple(
                evaluacion.publicada()                                     # D5 (RN007)
                for evaluacion in proyecto.evaluaciones))                  # D4
            for proyecto in self._repo.resultados_de_estudiante(estudiante_id))
