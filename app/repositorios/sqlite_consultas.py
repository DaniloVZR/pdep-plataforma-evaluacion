"""Consultas de solo lectura para el frontend (PDEP-35).

No aplican reglas de negocio ni escriben en la base de datos: devuelven
diccionarios listos para convertir a JSON. Por eso no pasan por los servicios
de HU-003, HU-005 y HU-007, cuyo flujo y caminos (RTF3) no cambian.
"""

from collections import defaultdict
import sqlite3


def _agrupar(filas: list[sqlite3.Row], clave: str, campos: tuple[str, ...]) -> dict:
    """Agrupa filas hijas por ``clave``: ``{id_padre: [{campo: valor}, ...]}``."""
    grupos: dict[int, list[dict]] = defaultdict(list)
    for fila in filas:
        grupos[fila[clave]].append({campo: fila[campo] for campo in campos})
    return grupos


class SqliteConsultaRepositorio:
    """Listados de la estructura académica, usuarios, equipos, ferias, rúbricas, proyectos y
    evaluaciones."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def _filas(self, sql: str, parametros: tuple = ()) -> list[sqlite3.Row]:
        return self._conexion.execute(sql, parametros).fetchall()

    def listar_programas(self) -> list[dict]:
        """Programas con sus asignaturas, para el formulario de registro (HU-003)."""
        asignaturas = _agrupar(
            self._filas("SELECT id, programa_id, codigo, nombre, semestre FROM asignatura "
                        "ORDER BY semestre, nombre"),
            "programa_id", ("id", "codigo", "nombre", "semestre"))
        return [
            {**dict(p), "asignaturas": asignaturas[p["id"]]}
            for p in self._filas("SELECT id, codigo, nombre, institucion_id, facultad_id, "
                                 "departamento_id FROM programa ORDER BY nombre")
        ]

    def existe_programa(self, programa_id: int) -> bool:
        """``True`` si el programa existe."""
        return bool(self._filas("SELECT 1 FROM programa WHERE id = ?", (programa_id,)))

    def listar_asignaturas(self, programa_id: int | None) -> list[dict]:
        """Asignaturas con su programa; si ``programa_id`` no es ``None``, solo las de ese
        programa (HU-002)."""
        sql = ("SELECT a.id, a.programa_id, p.nombre AS programa, a.codigo, a.nombre, "
               "a.semestre FROM asignatura a JOIN programa p ON p.id = a.programa_id")
        parametros: tuple = ()
        if programa_id is not None:
            sql += " WHERE a.programa_id = ?"
            parametros = (programa_id,)
        return [dict(fila) for fila in
                self._filas(sql + " ORDER BY a.semestre, a.nombre", parametros)]

    def listar_instituciones(self) -> list[dict]:
        """Instituciones con sus datos de contacto y dominios de correo (HU-001)."""
        dominios = _agrupar(
            self._filas("SELECT institucion_id, dominio FROM dominio_institucion "
                        "ORDER BY dominio"),
            "institucion_id", ("dominio",))
        return [
            {**dict(i), "dominios": [d["dominio"] for d in dominios[i["id"]]]}
            for i in self._filas("SELECT id, nombre, nit, correo_contacto, telefono "
                                 "FROM institucion ORDER BY nombre")
        ]

    def listar_unidades(self, tabla: str, institucion_id: int | None) -> list[dict]:
        """Facultades o departamentos (``tabla``); si ``institucion_id`` no es ``None``,
        solo los de esa institución (HU-001)."""
        sql = f"SELECT id, institucion_id, nombre FROM {tabla}"
        parametros: tuple = ()
        if institucion_id is not None:
            sql += " WHERE institucion_id = ?"
            parametros = (institucion_id,)
        return [dict(fila) for fila in self._filas(sql + " ORDER BY nombre", parametros)]

    def listar_usuarios(self, rol: str | None) -> list[dict]:
        """Usuarios registrados; si ``rol`` no es ``None``, solo los de ese rol."""
        sql = "SELECT id, nombres, correo, rol, programa_id FROM usuario"
        parametros: tuple = ()
        if rol is not None:
            sql += " WHERE rol = ?"
            parametros = (rol,)
        return [dict(fila) for fila in self._filas(sql + " ORDER BY nombres", parametros)]

    def listar_equipos(self) -> list[dict]:
        """Equipos con sus integrantes, para el formulario de inscripción (HU-005)."""
        integrantes = _agrupar(
            self._filas("SELECT ei.equipo_id, u.id, u.nombres FROM equipo_integrante ei "
                        "JOIN usuario u ON u.id = ei.usuario_id ORDER BY u.nombres"),
            "equipo_id", ("id", "nombres"))
        return [
            {"id": e["id"], "nombre": e["nombre"], "integrantes": integrantes[e["id"]]}
            for e in self._filas("SELECT id, nombre FROM equipo ORDER BY nombre")
        ]

    def listar_ferias(self) -> list[dict]:
        """Ferias con sus fechas y las asignaturas que participan (HU-005)."""
        asignaturas = _agrupar(
            self._filas("SELECT fa.feria_id, a.id, a.codigo, a.nombre FROM feria_asignatura fa "
                        "JOIN asignatura a ON a.id = fa.asignatura_id ORDER BY a.nombre"),
            "feria_id", ("id", "codigo", "nombre"))
        return [
            {"id": f["id"], "institucion_id": f["institucion_id"], "nombre": f["nombre"],
             "fecha_inicio": f["fecha_inicio"], "fecha_fin": f["fecha_fin"],
             "asignaturas": asignaturas[f["id"]]}
            for f in self._filas("SELECT id, institucion_id, nombre, fecha_inicio, fecha_fin "
                                 "FROM feria ORDER BY fecha_inicio DESC")
        ]

    def existe_feria(self, feria_id: int) -> bool:
        """``True`` si la feria existe."""
        return bool(self._filas("SELECT 1 FROM feria WHERE id = ?", (feria_id,)))

    def obtener_rubrica(self, feria_id: int) -> dict | None:
        """Escala y criterios de la rúbrica de la feria, o ``None`` si no tiene (HU-007)."""
        filas = self._filas("SELECT id, nota_minima, nota_maxima FROM rubrica "
                            "WHERE feria_id = ?", (feria_id,))
        if not filas:
            return None
        rubrica = filas[0]
        criterios = self._filas("SELECT id, nombre, peso FROM criterio WHERE rubrica_id = ? "
                                "ORDER BY id", (rubrica["id"],))
        return {"id": rubrica["id"], "feria_id": feria_id,
                "nota_minima": rubrica["nota_minima"], "nota_maxima": rubrica["nota_maxima"],
                "criterios": [dict(c) for c in criterios]}

    def listar_proyectos(self, feria_id: int | None) -> list[dict]:
        """Proyectos con sus asignaturas y evaluadores; si ``feria_id`` no es ``None``, de esa
        feria."""
        sql = ("SELECT p.id, p.nombre, p.descripcion, p.modalidad, p.fecha_inscripcion, "
               "p.feria_id, p.equipo_id, e.nombre AS equipo FROM proyecto p "
               "JOIN equipo e ON e.id = p.equipo_id")
        parametros: tuple = ()
        if feria_id is not None:
            sql += " WHERE p.feria_id = ?"
            parametros = (feria_id,)
        asignaturas = _agrupar(
            self._filas("SELECT proyecto_id, asignatura_id FROM proyecto_asignatura "
                        "ORDER BY asignatura_id"),
            "proyecto_id", ("asignatura_id",))
        evaluadores = _agrupar(
            self._filas("SELECT ev.proyecto_id, u.id, u.nombres FROM evaluacion ev "
                        "JOIN usuario u ON u.id = ev.evaluador_id ORDER BY u.nombres"),
            "proyecto_id", ("id", "nombres"))
        return [
            {**dict(p), "asignatura_ids": [a["asignatura_id"] for a in asignaturas[p["id"]]],
             "evaluadores": evaluadores[p["id"]]}
            for p in self._filas(sql + " ORDER BY p.id", parametros)
        ]

    def listar_carga_evaluadores(self) -> list[dict]:
        """Docentes con la cantidad de proyectos asignados y su estado (HU-006).

        Los docentes sin asignaciones aparecen con 0, para ver a quién repartir.
        """
        return [dict(fila) for fila in self._filas(
            "SELECT u.id, u.nombres, u.correo, COUNT(ev.id) AS asignados, "
            "COALESCE(SUM(ev.estado = 'PENDIENTE'), 0) AS pendientes, "
            "COALESCE(SUM(ev.estado = 'BORRADOR'), 0) AS borradores, "
            "COALESCE(SUM(ev.estado = 'CONFIRMADA'), 0) AS confirmadas "
            "FROM usuario u LEFT JOIN evaluacion ev ON ev.evaluador_id = u.id "
            "WHERE u.rol = 'DOCENTE' GROUP BY u.id ORDER BY asignados DESC, u.nombres")]

    def listar_evaluaciones(self, evaluador_id: int) -> list[dict]:
        """Evaluaciones asignadas al evaluador. El puntaje solo se incluye si está confirmada;
        la retroalimentación es del propio evaluador, así que la ve también en borrador."""
        filas = self._filas(
            "SELECT ev.id AS evaluacion_id, ev.proyecto_id, p.nombre AS proyecto, p.feria_id, "
            "f.nombre AS feria, ev.estado, ev.puntaje_final, ev.fecha_confirmacion, "
            "ev.retroalimentacion "
            "FROM evaluacion ev JOIN proyecto p ON p.id = ev.proyecto_id "
            "JOIN feria f ON f.id = p.feria_id WHERE ev.evaluador_id = ? ORDER BY ev.id",
            (evaluador_id,))
        return [
            {**dict(f), "puntaje_final": f["puntaje_final"] if f["estado"] == "CONFIRMADA"
             else None}
            for f in filas
        ]
