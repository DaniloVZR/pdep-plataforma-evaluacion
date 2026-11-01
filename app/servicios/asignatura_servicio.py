"""Caso de uso HU-002: registrar asignaturas y asociarlas a un programa académico."""

from app.dominio.errores import (
    AsignaturaDuplicadaError,
    ConflictoUnicidadError,
    ProgramaNoEncontradoError,
)
from app.dominio.modelos import Asignatura
from app.repositorios.contratos import ProgramaRepositorio, RegistroAsignaturaRepositorio
from app.validadores.asignatura_validador import validar_datos_asignatura
from app.validadores.estructura_validador import limpiar_texto


class RegistroAsignaturaServicio:
    """Coordina la validación, la existencia del programa y el guardado de la asignatura."""

    def __init__(self, programa_repo: ProgramaRepositorio,
                 asignatura_repo: RegistroAsignaturaRepositorio) -> None:
        self._programa_repo = programa_repo
        self._asignatura_repo = asignatura_repo

    def registrar(self, datos: object) -> Asignatura:
        """REQ-4. 400 si falta un dato, 404 si el programa no existe, 409 si el código existe."""
        validar_datos_asignatura(datos)                                  # D1
        if not self._programa_repo.existe(datos["programa_id"]):         # D2
            raise ProgramaNoEncontradoError("El programa académico indicado no existe.")
        asignatura = Asignatura(
            id=None,
            programa_id=datos["programa_id"],
            codigo=datos["codigo"].strip().upper(),
            nombre=limpiar_texto(datos["nombre"]),
            semestre=datos["semestre"],
        )
        try:
            return self._asignatura_repo.guardar(asignatura)
        except ConflictoUnicidadError as error:                           # D3
            raise AsignaturaDuplicadaError(
                "Ya existe una asignatura con ese código.") from error
