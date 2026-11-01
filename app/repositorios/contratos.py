"""Contratos (interfaces) que los servicios esperan de los repositorios.

Los servicios reciben estos objetos por el constructor. En producción se
inyectan las clases de ``sqlite_repositorios``; en las pruebas unitarias se
inyectan ``unittest.mock.Mock(spec=...)`` construidos a partir de estos
mismos contratos, así una prueba falla si llama a un método que no existe.
"""

from typing import Protocol

from app.dominio.modelos import (
    Asignacion,
    Asignatura,
    Cuenta,
    Departamento,
    Evaluacion,
    Facultad,
    Feria,
    Institucion,
    Programa,
    Proyecto,
    ResultadoProyecto,
    Rubrica,
    Usuario,
)


class InstitucionRepositorio(Protocol):
    """Acceso a las instituciones registradas."""

    def listar_dominios(self) -> frozenset[str]:
        """Dominios de correo de todas las instituciones activas, en minúsculas."""


class ProgramaRepositorio(Protocol):
    """Acceso a los programas académicos."""

    def existe(self, programa_id: int) -> bool:
        """``True`` si el programa existe."""


class AsignaturaRepositorio(Protocol):
    """Acceso a las asignaturas."""

    def ids_existentes(self, asignatura_ids: tuple[int, ...]) -> frozenset[int]:
        """Subconjunto de ``asignatura_ids`` que existe en la base de datos."""


class RegistroAsignaturaRepositorio(Protocol):
    """Registro de asignaturas (HU-002)."""

    def guardar(self, asignatura: Asignatura) -> Asignatura:
        """Inserta la asignatura.

        Lanza ``ConflictoUnicidadError`` si la base de datos rechaza el código por duplicado.
        """


class UsuarioRepositorio(Protocol):
    """Acceso a los usuarios."""

    def existe_correo(self, correo: str) -> bool:
        """``True`` si ya hay un usuario con ese correo."""

    def guardar(self, usuario: Usuario) -> Usuario:
        """Inserta el usuario y sus asignaturas en una transacción.

        Lanza ``ConflictoUnicidadError`` si la base de datos rechaza el correo
        por duplicado.
        """


class EquipoRepositorio(Protocol):
    """Acceso a los equipos."""

    def existe(self, equipo_id: int) -> bool:
        """``True`` si el equipo existe."""


class FeriaRepositorio(Protocol):
    """Acceso a las ferias."""

    def obtener(self, feria_id: int) -> Feria | None:
        """La feria con sus asignaturas participantes, o ``None``."""


class ProyectoRepositorio(Protocol):
    """Acceso a los proyectos inscritos."""

    def existe_en_feria(self, equipo_id: int, nombre_normalizado: str, feria_id: int) -> bool:
        """``True`` si el equipo ya inscribió ese nombre de proyecto en la feria."""

    def registrar(self, proyecto: Proyecto, nombre_normalizado: str) -> Proyecto:
        """Inserta el proyecto y sus asignaturas en una transacción.

        Lanza ``ConflictoUnicidadError`` si otra solicitud inscribió el mismo
        proyecto un instante antes.
        """


class EvaluacionRepositorio(Protocol):
    """Acceso a las evaluaciones."""

    def obtener_asignada(self, evaluador_id: int, proyecto_id: int) -> Evaluacion | None:
        """La evaluación creada al asignar el evaluador al proyecto, o ``None``."""

    def guardar_calificacion(self, evaluacion: Evaluacion) -> Evaluacion:
        """Actualiza estado, puntaje y fecha, y reemplaza las notas por criterio."""


class RubricaRepositorio(Protocol):
    """Acceso a las rúbricas."""

    def obtener_por_feria(self, feria_id: int) -> Rubrica | None:
        """La rúbrica de la feria con sus criterios, o ``None``."""


class EstructuraRepositorio(Protocol):
    """Acceso a la estructura académica: instituciones, facultades, departamentos y programas
    (HU-001).

    Los métodos ``guardar_*`` lanzan ``ConflictoUnicidadError`` si la base de datos rechaza
    el registro por duplicado.
    """

    def existe_institucion(self, institucion_id: int) -> bool:
        """``True`` si la institución existe."""

    def institucion_de_facultad(self, facultad_id: int) -> int | None:
        """Id de la institución de la facultad, o ``None`` si la facultad no existe."""

    def institucion_de_departamento(self, departamento_id: int) -> int | None:
        """Id de la institución del departamento, o ``None`` si no existe."""

    def guardar_institucion(self, institucion: Institucion) -> Institucion:
        """Inserta la institución y, si trae dominio, su dominio de correo."""

    def guardar_facultad(self, facultad: Facultad) -> Facultad:
        """Inserta la facultad."""

    def guardar_departamento(self, departamento: Departamento) -> Departamento:
        """Inserta el departamento."""

    def guardar_programa(self, programa: Programa) -> Programa:
        """Inserta el programa."""


class AsignacionRepositorio(Protocol):
    """Acceso a la asignación de evaluadores a proyectos (HU-006)."""

    def existe_proyecto(self, proyecto_id: int) -> bool:
        """``True`` si el proyecto existe."""

    def roles_de_usuarios(self, usuario_ids: tuple[int, ...]) -> dict[int, str]:
        """``{usuario_id: rol}`` de los usuarios que existen entre ``usuario_ids``."""

    def evaluadores_asignados(self, proyecto_id: int) -> frozenset[int]:
        """Ids de los evaluadores que ya tienen asignado el proyecto."""

    def asignar(self, proyecto_id: int,
                evaluador_ids: tuple[int, ...]) -> tuple[Asignacion, ...]:
        """Crea una evaluación PENDIENTE por evaluador, todas en una sola transacción.

        Lanza ``ConflictoUnicidadError`` si otra solicitud asignó el mismo evaluador
        un instante antes (restricción UNIQUE de ``evaluacion``).
        """


class CuentaRepositorio(Protocol):
    """Cuentas de acceso a la plataforma (RNF-03)."""

    def buscar_por_correo(self, correo: str) -> Cuenta | None:
        """Cuenta del correo (ya normalizado) con el nombre de su usuario, o ``None``."""


class CreacionFeriaRepositorio(Protocol):
    """Creación de ferias con sus asignaturas y su rúbrica (HU-004)."""

    def existe_institucion(self, institucion_id: int) -> bool:
        """``True`` si la institución existe."""

    def asignaturas_de_institucion(self, institucion_id: int,
                                   asignatura_ids: tuple[int, ...]) -> frozenset[int]:
        """Subconjunto de ``asignatura_ids`` que existe y pertenece a la institución."""

    def guardar_feria(self, institucion_id: int, feria: Feria,
                      criterios: tuple[tuple[str, float], ...]) -> Feria:
        """Inserta la feria, sus asignaturas, su rúbrica y sus criterios en una transacción."""


class ResultadoRepositorio(Protocol):
    """Resultados de los proyectos de un estudiante (HU-009)."""

    def rol_de_usuario(self, usuario_id: int) -> str | None:
        """Rol del usuario (``ESTUDIANTE`` o ``DOCENTE``), o ``None`` si no existe."""

    def resultados_de_estudiante(self, usuario_id: int) -> tuple[ResultadoProyecto, ...]:
        """Proyectos de los equipos del estudiante con todas sus evaluaciones, sin ocultar
        nada: el servicio decide qué se publica (RN007)."""
