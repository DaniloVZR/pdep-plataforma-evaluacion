"""Implementación de los repositorios sobre SQLite.

Todas las escrituras pasan por ``transaccion``: si algo falla a mitad de la
operación, ``with conexion`` deshace todo (no quedan inscripciones a medias,
RNF-02) y el error de ``sqlite3`` se traduce a un error del dominio.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime
import logging
import sqlite3

from app.dominio.errores import ConflictoUnicidadError, ErrorPersistencia
from app.dominio.modelos import (
    Criterio,
    EstadoEvaluacion,
    Evaluacion,
    Feria,
    Proyecto,
    Rubrica,
    Usuario,
)

registro = logging.getLogger(__name__)


@contextmanager
def transaccion(conexion: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Confirma al salir sin errores; si hay error, deshace y lo traduce."""
    try:
        with conexion:
            yield conexion
    except sqlite3.IntegrityError as error:
        if "UNIQUE" in str(error):
            raise ConflictoUnicidadError(str(error)) from error
        registro.exception("Violación de integridad no esperada")
        raise ErrorPersistencia("No se pudo guardar: datos inconsistentes.") from error
    except sqlite3.Error as error:
        registro.exception("Error de base de datos")
        raise ErrorPersistencia("No se pudo completar la operación en la base de datos.") \
            from error


def _marcadores(cantidad: int) -> str:
    """``"?, ?, ?"`` para una consulta ``IN`` con ``cantidad`` parámetros."""
    return ", ".join("?" for _ in range(cantidad))


class SqliteInstitucionRepositorio:
    """Instituciones y sus dominios de correo."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def listar_dominios(self) -> frozenset[str]:
        """Dominios de las instituciones activas, en minúsculas."""
        filas = self._conexion.execute(
            "SELECT lower(d.dominio) AS dominio FROM dominio_institucion d "
            "JOIN institucion i ON i.id = d.institucion_id WHERE i.activa = 1"
        ).fetchall()
        return frozenset(fila["dominio"] for fila in filas)


class SqliteProgramaRepositorio:
    """Programas académicos."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def existe(self, programa_id: int) -> bool:
        """``True`` si el programa existe."""
        fila = self._conexion.execute(
            "SELECT 1 FROM programa WHERE id = ?", (programa_id,)).fetchone()
        return fila is not None


class SqliteAsignaturaRepositorio:
    """Asignaturas."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def ids_existentes(self, asignatura_ids: tuple[int, ...]) -> frozenset[int]:
        """Ids de ``asignatura_ids`` que existen. Una sola consulta con ``IN``."""
        if not asignatura_ids:
            return frozenset()
        filas = self._conexion.execute(
            f"SELECT id FROM asignatura WHERE id IN ({_marcadores(len(asignatura_ids))})",
            asignatura_ids,
        ).fetchall()
        return frozenset(fila["id"] for fila in filas)


class SqliteUsuarioRepositorio:
    """Usuarios y sus asignaturas."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def existe_correo(self, correo: str) -> bool:
        """``True`` si el correo (ya normalizado) está registrado."""
        fila = self._conexion.execute(
            "SELECT 1 FROM usuario WHERE correo = ?", (correo,)).fetchone()
        return fila is not None

    def guardar(self, usuario: Usuario) -> Usuario:
        """Inserta el usuario y sus asignaturas en una sola transacción."""
        with transaccion(self._conexion) as conexion:
            cursor = conexion.execute(
                "INSERT INTO usuario (nombres, correo, rol, programa_id) VALUES (?, ?, ?, ?)",
                (usuario.nombres, usuario.correo, usuario.rol.value, usuario.programa_id),
            )
            usuario_id = cursor.lastrowid
            conexion.executemany(
                "INSERT INTO usuario_asignatura (usuario_id, asignatura_id) VALUES (?, ?)",
                [(usuario_id, asignatura_id) for asignatura_id in usuario.asignatura_ids],
            )
        return Usuario(usuario_id, usuario.nombres, usuario.correo, usuario.rol,
                       usuario.programa_id, usuario.asignatura_ids)


class SqliteEquipoRepositorio:
    """Equipos."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def existe(self, equipo_id: int) -> bool:
        """``True`` si el equipo existe."""
        fila = self._conexion.execute(
            "SELECT 1 FROM equipo WHERE id = ?", (equipo_id,)).fetchone()
        return fila is not None


class SqliteFeriaRepositorio:
    """Ferias y sus asignaturas participantes."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def obtener(self, feria_id: int) -> Feria | None:
        """La feria con sus asignaturas, o ``None`` si no existe."""
        fila = self._conexion.execute(
            "SELECT id, nombre, fecha_inicio, fecha_fin FROM feria WHERE id = ?",
            (feria_id,)).fetchone()
        if fila is None:
            return None
        asignaturas = self._conexion.execute(
            "SELECT asignatura_id FROM feria_asignatura WHERE feria_id = ?",
            (feria_id,)).fetchall()
        return Feria(
            id=fila["id"],
            nombre=fila["nombre"],
            fecha_inicio=date.fromisoformat(fila["fecha_inicio"]),
            fecha_fin=date.fromisoformat(fila["fecha_fin"]),
            asignatura_ids=frozenset(a["asignatura_id"] for a in asignaturas),
        )


class SqliteProyectoRepositorio:
    """Proyectos inscritos en ferias."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def existe_en_feria(self, equipo_id: int, nombre_normalizado: str, feria_id: int) -> bool:
        """``True`` si el equipo ya inscribió ese nombre en la feria."""
        fila = self._conexion.execute(
            "SELECT 1 FROM proyecto WHERE equipo_id = ? AND nombre_normalizado = ? "
            "AND feria_id = ?", (equipo_id, nombre_normalizado, feria_id)).fetchone()
        return fila is not None

    def registrar(self, proyecto: Proyecto, nombre_normalizado: str) -> Proyecto:
        """Inserta el proyecto y sus asignaturas en una sola transacción."""
        with transaccion(self._conexion) as conexion:
            cursor = conexion.execute(
                "INSERT INTO proyecto (equipo_id, feria_id, nombre, nombre_normalizado, "
                "descripcion, modalidad, fecha_inscripcion) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (proyecto.equipo_id, proyecto.feria_id, proyecto.nombre, nombre_normalizado,
                 proyecto.descripcion, proyecto.modalidad.value,
                 proyecto.fecha_inscripcion.isoformat()),
            )
            proyecto_id = cursor.lastrowid
            conexion.executemany(
                "INSERT INTO proyecto_asignatura (proyecto_id, asignatura_id) VALUES (?, ?)",
                [(proyecto_id, asignatura_id) for asignatura_id in proyecto.asignatura_ids],
            )
        return Proyecto(proyecto_id, proyecto.equipo_id, proyecto.feria_id, proyecto.nombre,
                        proyecto.descripcion, proyecto.modalidad, proyecto.asignatura_ids,
                        proyecto.fecha_inscripcion)


class SqliteRubricaRepositorio:
    """Rúbricas y criterios."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def obtener_por_feria(self, feria_id: int) -> Rubrica | None:
        """La rúbrica de la feria con sus criterios, o ``None``."""
        fila = self._conexion.execute(
            "SELECT id, feria_id, nota_minima, nota_maxima FROM rubrica WHERE feria_id = ?",
            (feria_id,)).fetchone()
        if fila is None:
            return None
        criterios = self._conexion.execute(
            "SELECT id, nombre, peso FROM criterio WHERE rubrica_id = ? ORDER BY id",
            (fila["id"],)).fetchall()
        return Rubrica(
            id=fila["id"],
            feria_id=fila["feria_id"],
            nota_minima=fila["nota_minima"],
            nota_maxima=fila["nota_maxima"],
            criterios=tuple(Criterio(c["id"], c["nombre"], c["peso"]) for c in criterios),
        )


class SqliteEvaluacionRepositorio:
    """Evaluaciones y notas por criterio."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def obtener_asignada(self, evaluador_id: int, proyecto_id: int) -> Evaluacion | None:
        """La evaluación del evaluador para el proyecto, o ``None`` si no está asignado."""
        fila = self._conexion.execute(
            "SELECT e.id, e.proyecto_id, e.evaluador_id, p.feria_id, e.estado, "
            "e.puntaje_final, e.fecha_confirmacion FROM evaluacion e "
            "JOIN proyecto p ON p.id = e.proyecto_id "
            "WHERE e.evaluador_id = ? AND e.proyecto_id = ?",
            (evaluador_id, proyecto_id)).fetchone()
        if fila is None:
            return None
        fecha = fila["fecha_confirmacion"]
        return Evaluacion(
            id=fila["id"],
            proyecto_id=fila["proyecto_id"],
            evaluador_id=fila["evaluador_id"],
            feria_id=fila["feria_id"],
            estado=EstadoEvaluacion(fila["estado"]),
            puntaje_final=fila["puntaje_final"],
            fecha_confirmacion=datetime.fromisoformat(fecha) if fecha else None,
        )

    def guardar_calificacion(self, evaluacion: Evaluacion) -> Evaluacion:
        """Actualiza la evaluación y reemplaza sus notas en una sola transacción."""
        fecha = evaluacion.fecha_confirmacion
        with transaccion(self._conexion) as conexion:
            conexion.execute(
                "UPDATE evaluacion SET estado = ?, puntaje_final = ?, fecha_confirmacion = ? "
                "WHERE id = ?",
                (evaluacion.estado.value, evaluacion.puntaje_final,
                 fecha.isoformat() if fecha else None, evaluacion.id),
            )
            conexion.execute(
                "DELETE FROM calificacion_criterio WHERE evaluacion_id = ?", (evaluacion.id,))
            conexion.executemany(
                "INSERT INTO calificacion_criterio (evaluacion_id, criterio_id, nota) "
                "VALUES (?, ?, ?)",
                [(evaluacion.id, criterio_id, nota)
                 for criterio_id, nota in evaluacion.notas.items()],
            )
        return evaluacion
