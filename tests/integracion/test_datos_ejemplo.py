"""``flask init-db --ejemplo``: los datos de ejemplo cargan y son consistentes.

Si alguien amplía app/datos_ejemplo.sql, estas pruebas avisan si un puntaje no coincide
con la rúbrica, si un proyecto usa una asignatura que no participa en su feria o si la
modalidad no corresponde al número de asignaturas.
"""

import sqlite3

import pytest

from app import create_app
from app.db import abrir_conexion
from app.dominio.modelos import Criterio, Rubrica


@pytest.fixture(name="app_ejemplo")
def fixture_app_ejemplo(tmp_path):
    """Aplicación con una base nueva cargada con ``init-db --ejemplo``."""
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "ejemplo.sqlite3")})
    resultado = app.test_cli_runner().invoke(args=["init-db", "--ejemplo"])
    assert resultado.output.strip() == "Base de datos inicializada con datos de ejemplo."
    return app


@pytest.fixture(name="bd")
def fixture_bd(app_ejemplo):
    """Conexión directa a la base de ejemplo."""
    conexion = abrir_conexion(app_ejemplo.config["DATABASE"])
    yield conexion
    conexion.close()


def _contar(bd: sqlite3.Connection, sql: str) -> int:
    return bd.execute(sql).fetchone()[0]


def test_carga_los_datos_de_demostracion_y_los_de_ejemplo(bd):
    """Las cuentas de datos_demo.sql siguen y hay variedad para probar."""
    assert _contar(bd, "SELECT COUNT(*) FROM cuenta") == 5
    assert _contar(bd, "SELECT COUNT(*) FROM feria") == 2
    assert _contar(bd, "SELECT COUNT(*) FROM programa") == 3
    assert _contar(bd, "SELECT COUNT(*) FROM proyecto") == 11
    estados = dict(bd.execute(
        "SELECT estado, COUNT(*) FROM evaluacion GROUP BY estado").fetchall())
    assert estados == {"CONFIRMADA": 10, "BORRADOR": 1, "PENDIENTE": 2}


def test_cada_puntaje_coincide_con_su_rubrica(bd):
    """El puntaje guardado es el que calcula HU-007 con las notas y los pesos (RN006)."""
    evaluaciones = bd.execute(
        "SELECT ev.id, ev.puntaje_final, p.feria_id FROM evaluacion ev "
        "JOIN proyecto p ON p.id = ev.proyecto_id WHERE ev.estado != 'PENDIENTE'").fetchall()
    assert evaluaciones
    for evaluacion in evaluaciones:
        rubrica = bd.execute("SELECT * FROM rubrica WHERE feria_id = ?",
                             (evaluacion["feria_id"],)).fetchone()
        criterios = tuple(Criterio(c["id"], c["nombre"], c["peso"]) for c in bd.execute(
            "SELECT * FROM criterio WHERE rubrica_id = ? ORDER BY id", (rubrica["id"],)))
        notas = dict(bd.execute(
            "SELECT criterio_id, nota FROM calificacion_criterio WHERE evaluacion_id = ?",
            (evaluacion["id"],)).fetchall())
        rubrica = Rubrica(rubrica["id"], evaluacion["feria_id"], rubrica["nota_minima"],
                          rubrica["nota_maxima"], criterios)
        assert rubrica.pesos_validos()
        assert set(notas) == rubrica.ids_criterios(), f"evaluación {evaluacion['id']}"
        assert rubrica.calcular_puntaje(notas) == evaluacion["puntaje_final"], \
            f"evaluación {evaluacion['id']}"


def test_proyectos_respetan_feria_y_modalidad(bd):
    """Cada asignatura participa en la feria del proyecto; PA tiene una, PIA dos o más."""
    fuera_de_la_feria = _contar(bd, (
        "SELECT COUNT(*) FROM proyecto_asignatura pa JOIN proyecto p ON p.id = pa.proyecto_id "
        "WHERE NOT EXISTS (SELECT 1 FROM feria_asignatura fa "
        "WHERE fa.feria_id = p.feria_id AND fa.asignatura_id = pa.asignatura_id)"))
    assert fuera_de_la_feria == 0
    for proyecto in bd.execute(
            "SELECT p.id, p.modalidad, COUNT(*) AS cantidad FROM proyecto p "
            "JOIN proyecto_asignatura pa ON pa.proyecto_id = p.id GROUP BY p.id"):
        esperado = proyecto["cantidad"] == 1 if proyecto["modalidad"] == "PA" \
            else proyecto["cantidad"] >= 2
        assert esperado, f"proyecto {proyecto['id']}"


def test_el_reporte_muestra_todos_los_niveles(app_ejemplo):
    """Con los datos de ejemplo, el reporte de HU-010 tiene proyectos en los cuatro niveles
    y pendientes de los tres tipos."""
    cliente = app_ejemplo.test_client()
    token = cliente.post("/api/login", json={"correo": "admin@pascualbravo.edu.co",
                                             "clave": "admin123"}).get_json()["token"]
    reporte = cliente.get("/api/reportes", headers={"Authorization": f"Bearer {token}"}
                          ).get_json()
    distribucion = reporte["distribucion"]
    assert all(distribucion[nivel] > 0
               for nivel in ("excelente", "bueno", "aceptable", "insuficiente"))
    assert [g["nombre"] for g in reporte["grupos"]] == ["Feria de Proyectos 2026-1",
                                                       "Feria de Proyectos 2026-2"]
    avance = reporte["avance"]
    assert (avance["borradores"], avance["sin_empezar"],
            avance["proyectos_sin_evaluador"]) == (1, 2, 1)


def test_las_cuentas_nuevas_inician_sesion(app_ejemplo):
    """La segunda evaluadora y la segunda estudiante pueden entrar."""
    cliente = app_ejemplo.test_client()
    for correo, clave, rol in (
            ("carolina.restrepo@pascualbravo.edu.co", "evaluador123", "EVALUADOR"),
            ("laura.gomez@pascualbravo.edu.co", "estudiante123", "ESTUDIANTE")):
        respuesta = cliente.post("/api/login", json={"correo": correo, "clave": clave})
        assert (respuesta.status_code, respuesta.get_json()["rol"]) == (200, rol)
