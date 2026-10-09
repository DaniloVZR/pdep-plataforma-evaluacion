"""Contratos (interfaces) que los servicios esperan de los repositorios.

Los servicios reciben estos objetos por el constructor. En producción se
inyectan las clases de ``sqlite_repositorios``; en las pruebas unitarias se
inyectan ``unittest.mock.Mock(spec=...)`` construidos a partir de estos
mismos contratos, así una prueba falla si llama a un método que no existe.
"""

from typing import Protocol

from app.dominio.modelos import Evaluacion, Feria, Proyecto, Rubrica, Usuario


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
