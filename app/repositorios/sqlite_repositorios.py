"""Implementación de los repositorios sobre SQLite.

Todas las escrituras pasan por ``transaccion``: si algo falla a mitad de la
operación, ``with conexion`` deshace todo (no quedan inscripciones a medias,
RNF-02) y el error de ``sqlite3`` se traduce a un error del dominio.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from datetime import date, datetime
import logging
import sqlite3

from app.dominio.errores import ConflictoUnicidadError, ErrorPersistencia
from app.dominio.modelos import (
    NOTA_MAXIMA,
    NOTA_MINIMA,
    Asignacion,
    Asignatura,
    Criterio,
    Cuenta,
    Departamento,
    EstadoEvaluacion,
    Evaluacion,
    Facultad,
    Feria,
    Institucion,
    Programa,
    Proyecto,
    ResultadoEvaluacion,
    ResultadoProyecto,
    RolCuenta,
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


class SqliteRegistroAsignaturaRepositorio:
    """Registro de asignaturas (HU-002)."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def guardar(self, asignatura: Asignatura) -> Asignatura:
        """Inserta la asignatura; el código repetido lo rechaza la restricción UNIQUE."""
        with transaccion(self._conexion) as conexion:
            cursor = conexion.execute(
                "INSERT INTO asignatura (programa_id, codigo, nombre, semestre) "
                "VALUES (?, ?, ?, ?)",
                (asignatura.programa_id, asignatura.codigo, asignatura.nombre,
                 asignatura.semestre))
        return replace(asignatura, id=cursor.lastrowid)


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
            "e.puntaje_final, e.fecha_confirmacion, e.retroalimentacion FROM evaluacion e "
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
            retroalimentacion=fila["retroalimentacion"],
        )

    def guardar_calificacion(self, evaluacion: Evaluacion) -> Evaluacion:
        """Actualiza la evaluación y reemplaza sus notas en una sola transacción."""
        fecha = evaluacion.fecha_confirmacion
        with transaccion(self._conexion) as conexion:
            conexion.execute(
                "UPDATE evaluacion SET estado = ?, puntaje_final = ?, fecha_confirmacion = ?, "
                "retroalimentacion = ? WHERE id = ?",
                (evaluacion.estado.value, evaluacion.puntaje_final,
                 fecha.isoformat() if fecha else None, evaluacion.retroalimentacion,
                 evaluacion.id),
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


class SqliteEstructuraRepositorio:
    """Instituciones, facultades, departamentos y programas (HU-001)."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def _institucion_de(self, tabla: str, fila_id: int) -> int | None:
        fila = self._conexion.execute(
            f"SELECT institucion_id FROM {tabla} WHERE id = ?", (fila_id,)).fetchone()
        return None if fila is None else fila["institucion_id"]

    def existe_institucion(self, institucion_id: int) -> bool:
        """``True`` si la institución existe."""
        fila = self._conexion.execute(
            "SELECT 1 FROM institucion WHERE id = ?", (institucion_id,)).fetchone()
        return fila is not None

    def institucion_de_facultad(self, facultad_id: int) -> int | None:
        """Id de la institución de la facultad, o ``None`` si no existe."""
        return self._institucion_de("facultad", facultad_id)

    def institucion_de_departamento(self, departamento_id: int) -> int | None:
        """Id de la institución del departamento, o ``None`` si no existe."""
        return self._institucion_de("departamento", departamento_id)

    def guardar_institucion(self, institucion: Institucion) -> Institucion:
        """Inserta la institución y su dominio en una sola transacción."""
        with transaccion(self._conexion) as conexion:
            cursor = conexion.execute(
                "INSERT INTO institucion (nombre, nit, correo_contacto, telefono) "
                "VALUES (?, ?, ?, ?)",
                (institucion.nombre, institucion.nit, institucion.correo_contacto,
                 institucion.telefono),
            )
            if institucion.dominio:
                conexion.execute(
                    "INSERT INTO dominio_institucion (institucion_id, dominio) VALUES (?, ?)",
                    (cursor.lastrowid, institucion.dominio))
        return replace(institucion, id=cursor.lastrowid)

    def guardar_facultad(self, facultad: Facultad) -> Facultad:
        """Inserta la facultad."""
        with transaccion(self._conexion) as conexion:
            cursor = conexion.execute(
                "INSERT INTO facultad (institucion_id, nombre) VALUES (?, ?)",
                (facultad.institucion_id, facultad.nombre))
        return replace(facultad, id=cursor.lastrowid)

    def guardar_departamento(self, departamento: Departamento) -> Departamento:
        """Inserta el departamento."""
        with transaccion(self._conexion) as conexion:
            cursor = conexion.execute(
                "INSERT INTO departamento (institucion_id, nombre) VALUES (?, ?)",
                (departamento.institucion_id, departamento.nombre))
        return replace(departamento, id=cursor.lastrowid)

    def guardar_programa(self, programa: Programa) -> Programa:
        """Inserta el programa."""
        with transaccion(self._conexion) as conexion:
            cursor = conexion.execute(
                "INSERT INTO programa (institucion_id, facultad_id, departamento_id, codigo, "
                "nombre) VALUES (?, ?, ?, ?, ?)",
                (programa.institucion_id, programa.facultad_id, programa.departamento_id,
                 programa.codigo, programa.nombre))
        return replace(programa, id=cursor.lastrowid)


class SqliteAsignacionRepositorio:
    """Asignación de evaluadores a proyectos (HU-006)."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def existe_proyecto(self, proyecto_id: int) -> bool:
        """``True`` si el proyecto existe."""
        fila = self._conexion.execute(
            "SELECT 1 FROM proyecto WHERE id = ?", (proyecto_id,)).fetchone()
        return fila is not None

    def roles_de_usuarios(self, usuario_ids: tuple[int, ...]) -> dict[int, str]:
        """``{id: rol}`` de los usuarios que existen. Una sola consulta con ``IN``."""
        filas = self._conexion.execute(
            f"SELECT id, rol FROM usuario WHERE id IN ({_marcadores(len(usuario_ids))})",
            usuario_ids,
        ).fetchall()
        return {fila["id"]: fila["rol"] for fila in filas}

    def evaluadores_asignados(self, proyecto_id: int) -> frozenset[int]:
        """Evaluadores que ya tienen una evaluación del proyecto."""
        filas = self._conexion.execute(
            "SELECT evaluador_id FROM evaluacion WHERE proyecto_id = ?",
            (proyecto_id,)).fetchall()
        return frozenset(fila["evaluador_id"] for fila in filas)

    def asignar(self, proyecto_id: int,
                evaluador_ids: tuple[int, ...]) -> tuple[Asignacion, ...]:
        """Inserta una evaluación PENDIENTE por evaluador; si una falla, no queda ninguna."""
        asignaciones = []
        with transaccion(self._conexion) as conexion:
            for evaluador_id in evaluador_ids:
                cursor = conexion.execute(
                    "INSERT INTO evaluacion (proyecto_id, evaluador_id) VALUES (?, ?)",
                    (proyecto_id, evaluador_id))
                asignaciones.append(Asignacion(cursor.lastrowid, proyecto_id, evaluador_id))
        return tuple(asignaciones)


class SqliteCuentaRepositorio:
    """Cuentas de acceso (RNF-03). Solo lectura: las cuentas se cargan con los datos de prueba."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def buscar_por_correo(self, correo: str) -> Cuenta | None:
        """Cuenta del correo con el nombre del usuario; el administrador no tiene usuario."""
        fila = self._conexion.execute(
            """
            SELECT c.correo, c.clave, c.rol, c.usuario_id,
                   COALESCE(u.nombres, 'Administración') AS nombre
            FROM cuenta c LEFT JOIN usuario u ON u.id = c.usuario_id
            WHERE c.correo = ?
            """,
            (correo,),
        ).fetchone()
        if fila is None:
            return None
        return Cuenta(fila["correo"], fila["clave"], RolCuenta(fila["rol"]),
                      fila["usuario_id"], fila["nombre"])


class SqliteCreacionFeriaRepositorio:
    """Creación de ferias con sus asignaturas y su rúbrica (HU-004)."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def existe_institucion(self, institucion_id: int) -> bool:
        """``True`` si la institución existe."""
        fila = self._conexion.execute(
            "SELECT 1 FROM institucion WHERE id = ?", (institucion_id,)).fetchone()
        return fila is not None

    def asignaturas_de_institucion(self, institucion_id: int,
                                   asignatura_ids: tuple[int, ...]) -> frozenset[int]:
        """Asignaturas que existen y cuyo programa es de la institución. Una sola consulta."""
        filas = self._conexion.execute(
            "SELECT a.id FROM asignatura a JOIN programa p ON p.id = a.programa_id "
            f"WHERE p.institucion_id = ? AND a.id IN ({_marcadores(len(asignatura_ids))})",
            (institucion_id, *asignatura_ids),
        ).fetchall()
        return frozenset(fila["id"] for fila in filas)

    def guardar_feria(self, institucion_id: int, feria: Feria,
                      criterios: tuple[tuple[str, float], ...]) -> Feria:
        """Feria, asignaturas, rúbrica (escala 1.0 a 5.0) y criterios: todo o nada."""
        with transaccion(self._conexion) as conexion:
            feria_id = conexion.execute(
                "INSERT INTO feria (institucion_id, nombre, fecha_inicio, fecha_fin) "
                "VALUES (?, ?, ?, ?)",
                (institucion_id, feria.nombre, feria.fecha_inicio.isoformat(),
                 feria.fecha_fin.isoformat()),
            ).lastrowid
            conexion.executemany(
                "INSERT INTO feria_asignatura (feria_id, asignatura_id) VALUES (?, ?)",
                [(feria_id, asignatura_id) for asignatura_id in sorted(feria.asignatura_ids)])
            rubrica_id = conexion.execute(
                "INSERT INTO rubrica (feria_id, nota_minima, nota_maxima) VALUES (?, ?, ?)",
                (feria_id, NOTA_MINIMA, NOTA_MAXIMA)).lastrowid
            conexion.executemany(
                "INSERT INTO criterio (rubrica_id, nombre, peso) VALUES (?, ?, ?)",
                [(rubrica_id, nombre, peso) for nombre, peso in criterios])
        return replace(feria, id=feria_id)


class SqliteResultadoRepositorio:
    """Resultados de los proyectos de un estudiante (HU-009). Solo lectura."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def rol_de_usuario(self, usuario_id: int) -> str | None:
        """Rol del usuario, o ``None`` si no existe."""
        fila = self._conexion.execute(
            "SELECT rol FROM usuario WHERE id = ?", (usuario_id,)).fetchone()
        return None if fila is None else fila["rol"]

    def resultados_de_estudiante(self, usuario_id: int) -> tuple[ResultadoProyecto, ...]:
        """Dos consultas: los proyectos de sus equipos y las evaluaciones de esos proyectos."""
        proyectos = self._conexion.execute(
            "SELECT p.id, p.nombre, f.nombre AS feria, e.nombre AS equipo FROM proyecto p "
            "JOIN equipo e ON e.id = p.equipo_id JOIN feria f ON f.id = p.feria_id "
            "JOIN equipo_integrante ei ON ei.equipo_id = p.equipo_id "
            "WHERE ei.usuario_id = ? ORDER BY p.id", (usuario_id,)).fetchall()
        evaluaciones = self._conexion.execute(
            "SELECT ev.id, ev.proyecto_id, u.nombres AS evaluador, ev.estado, "
            "ev.puntaje_final, ev.retroalimentacion, ev.fecha_confirmacion "
            "FROM evaluacion ev JOIN usuario u ON u.id = ev.evaluador_id "
            "JOIN proyecto p ON p.id = ev.proyecto_id "
            "JOIN equipo_integrante ei ON ei.equipo_id = p.equipo_id "
            "WHERE ei.usuario_id = ? ORDER BY ev.id", (usuario_id,)).fetchall()
        por_proyecto: dict[int, list[ResultadoEvaluacion]] = {p["id"]: [] for p in proyectos}
        for fila in evaluaciones:
            fecha = fila["fecha_confirmacion"]
            por_proyecto[fila["proyecto_id"]].append(ResultadoEvaluacion(
                evaluacion_id=fila["id"],
                evaluador=fila["evaluador"],
                estado=EstadoEvaluacion(fila["estado"]),
                puntaje_final=fila["puntaje_final"],
                retroalimentacion=fila["retroalimentacion"],
                fecha_confirmacion=datetime.fromisoformat(fecha) if fecha else None,
            ))
        return tuple(
            ResultadoProyecto(p["id"], p["nombre"], p["feria"], p["equipo"],
                              tuple(por_proyecto[p["id"]]))
            for p in proyectos)
