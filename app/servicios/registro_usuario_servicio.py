"""Caso de uso HU-003: registrar estudiantes y docentes."""

from app.dominio.errores import (
    AsignaturaNoEncontradaError,
    ConflictoUnicidadError,
    CorreoDuplicadoError,
    CorreoNoInstitucionalError,
    ProgramaNoEncontradoError,
)
from app.dominio.modelos import Rol, Usuario
from app.repositorios.contratos import (
    AsignaturaRepositorio,
    InstitucionRepositorio,
    ProgramaRepositorio,
    UsuarioRepositorio,
)
from app.validadores.usuario_validador import (
    dominio_es_institucional,
    normalizar_correo,
    validar_datos_registro,
)


class RegistroUsuarioServicio:
    """Coordina las validaciones y el guardado de un usuario nuevo."""

    def __init__(self, institucion_repo: InstitucionRepositorio,
                 programa_repo: ProgramaRepositorio,
                 asignatura_repo: AsignaturaRepositorio,
                 usuario_repo: UsuarioRepositorio) -> None:
        self._institucion_repo = institucion_repo
        self._programa_repo = programa_repo
        self._asignatura_repo = asignatura_repo
        self._usuario_repo = usuario_repo

    def registrar(self, datos: object) -> Usuario:
        """Valida los datos y guarda el usuario. Cada regla incumplida lanza su error.

        Las validaciones van de la más barata a la más costosa: primero las que
        solo miran ``datos`` y después las que consultan la base de datos.
        """
        validar_datos_registro(datos)                                    # D1
        correo = normalizar_correo(datos["correo"])
        if not dominio_es_institucional(correo, self._institucion_repo.listar_dominios()):
            raise CorreoNoInstitucionalError(                           # D2
                "El correo no pertenece a una institución registrada.")
        if self._usuario_repo.existe_correo(correo):                     # D3
            raise CorreoDuplicadoError("Ya existe un usuario con ese correo.")
        if not self._programa_repo.existe(datos["programa_id"]):         # D4
            raise ProgramaNoEncontradoError("El programa indicado no existe.")
        asignatura_ids = tuple(dict.fromkeys(datos.get("asignatura_ids", [])))
        faltantes = set(asignatura_ids) - self._asignatura_repo.ids_existentes(asignatura_ids)
        if faltantes:                                                    # D5
            raise AsignaturaNoEncontradaError(
                f"No existen las asignaturas {sorted(faltantes)}.")
        usuario = Usuario(
            id=None,
            nombres=datos["nombres"].strip(),
            correo=correo,
            rol=Rol(datos["rol"].strip().upper()),
            programa_id=datos["programa_id"],
            asignatura_ids=asignatura_ids,
        )
        try:
            return self._usuario_repo.guardar(usuario)
        except ConflictoUnicidadError as error:                           # D6
            raise CorreoDuplicadoError("Ya existe un usuario con ese correo.") from error
