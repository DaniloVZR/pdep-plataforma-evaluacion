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
    """Listados de programas, usuarios, equipos, ferias, rúbricas, proyectos y evaluaciones."""

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
            {"id": p["id"], "codigo": p["codigo"], "nombre": p["nombre"],
             "asignaturas": asignaturas[p["id"]]}
            for p in self._filas("SELECT id, codigo, nombre FROM programa ORDER BY nombre")
        ]

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
            {"id": f["id"], "nombre": f["nombre"], "fecha_inicio": f["fecha_inicio"],
             "fecha_fin": f["fecha_fin"], "asignaturas": asignaturas[f["id"]]}
            for f in self._filas("SELECT id, nombre, fecha_inicio, fecha_fin FROM feria "
                                 "ORDER BY fecha_inicio DESC")
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
        """Proyectos inscritos con sus asignaturas; si ``feria_id`` no es ``None``, de esa feria."""
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
        return [
            {**dict(p), "asignatura_ids": [a["asignatura_id"] for a in asignaturas[p["id"]]]}
            for p in self._filas(sql + " ORDER BY p.id", parametros)
        ]

    def listar_evaluaciones(self, evaluador_id: int) -> list[dict]:
        """Evaluaciones asignadas al evaluador. El puntaje solo se incluye si está confirmada."""
        filas = self._filas(
            "SELECT ev.id AS evaluacion_id, ev.proyecto_id, p.nombre AS proyecto, p.feria_id, "
            "f.nombre AS feria, ev.estado, ev.puntaje_final, ev.fecha_confirmacion "
            "FROM evaluacion ev JOIN proyecto p ON p.id = ev.proyecto_id "
            "JOIN feria f ON f.id = p.feria_id WHERE ev.evaluador_id = ? ORDER BY ev.id",
            (evaluador_id,))
        return [
            {**dict(f), "puntaje_final": f["puntaje_final"] if f["estado"] == "CONFIRMADA"
             else None}
            for f in filas
        ]
