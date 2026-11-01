"""HU-004 · ``POST /api/ferias`` contra la base temporal.

Datos de partida (app/datos_demo.sql): institución 1 con las asignaturas 1, 2 y 3 y la
feria 1. La rúbrica de la feria nueva debe quedar lista para calificar con HU-007.
"""

from datetime import date

import pytest

from app.dominio.errores import ErrorPersistencia
from app.dominio.modelos import Feria
from app.repositorios.sqlite_repositorios import SqliteCreacionFeriaRepositorio

FERIA = {
    "institucion_id": 1, "nombre": "Feria 2027-1", "fecha_inicio": "2027-03-01",
    "fecha_fin": "2027-03-15", "asignatura_ids": [2, 3],
    "criterios": [{"nombre": "Funcionalidad", "peso": 0.6},
                  {"nombre": "Presentación", "peso": 0.4}],
}


def test_feria_creada_aparece_en_el_listado_con_su_rubrica(cliente):
    """201, la feria se lista con sus asignaturas y su rúbrica tiene los criterios enviados."""
    respuesta = cliente.post("/api/ferias", json=FERIA)
    assert respuesta.status_code == 201
    creada = respuesta.get_json()
    assert creada["asignatura_ids"] == [2, 3]

    listada = next(f for f in cliente.get("/api/ferias").get_json() if f["id"] == creada["id"])
    assert listada["institucion_id"] == 1
    assert [a["id"] for a in listada["asignaturas"]] == [2, 3]

    rubrica = cliente.get(f"/api/ferias/{creada['id']}/rubrica").get_json()
    assert (rubrica["nota_minima"], rubrica["nota_maxima"]) == (1.0, 5.0)
    assert [(c["nombre"], c["peso"]) for c in rubrica["criterios"]] == \
        [("Funcionalidad", 0.6), ("Presentación", 0.4)]


@pytest.mark.parametrize("cambios, estado, codigo", [
    pytest.param({"fecha_fin": "2027-03-01"}, 422, "fechas_feria_invalidas", id="fin-igual"),
    pytest.param({"asignatura_ids": [99]}, 404, "asignatura_no_encontrada", id="asignatura"),
    pytest.param({"institucion_id": 9}, 404, "institucion_no_encontrada", id="institucion"),
    pytest.param({"criterios": [{"nombre": "A", "peso": 0.5}]}, 422, "pesos_invalidos",
                 id="pesos"),
    pytest.param({"asignatura_ids": []}, 400, "dato_invalido", id="sin-asignaturas"),
])
def test_rechazos_no_crean_ninguna_feria(cliente, cambios, estado, codigo):
    """Cada rechazo responde su código HTTP y el listado sigue con la feria de demostración."""
    respuesta = cliente.post("/api/ferias", json={**FERIA, **cambios})
    assert respuesta.status_code == estado
    assert respuesta.get_json()["codigo"] == codigo
    assert len(cliente.get("/api/ferias").get_json()) == 1


def test_asignaturas_de_otra_institucion_no_cuentan(conexion):
    """Solo cuentan las asignaturas cuyo programa es de la institución pedida."""
    conexion.executescript("""
        INSERT INTO institucion (id, nombre, nit) VALUES (2, 'Otra', '900');
        INSERT INTO facultad (id, institucion_id, nombre) VALUES (2, 2, 'Facultad');
        INSERT INTO programa (id, institucion_id, facultad_id, codigo, nombre)
            VALUES (2, 2, 2, 'OTR', 'Otro programa');
        INSERT INTO asignatura (id, programa_id, codigo, nombre, semestre)
            VALUES (4, 2, 'OT1', 'Otra asignatura', 1);
    """)
    repo = SqliteCreacionFeriaRepositorio(conexion)
    assert repo.asignaturas_de_institucion(1, (1, 4)) == frozenset({1})
    assert repo.asignaturas_de_institucion(2, (1, 4)) == frozenset({4})


def test_guardar_feria_es_todo_o_nada(conexion):
    """Si un criterio falla (peso nulo), se hace ROLLBACK: no queda la feria ni su rúbrica."""
    repo = SqliteCreacionFeriaRepositorio(conexion)
    antes = conexion.execute("SELECT COUNT(*) FROM feria").fetchone()[0]
    feria = Feria(0, "Rota", date(2027, 1, 1), date(2027, 1, 2), frozenset({1}))
    with pytest.raises(ErrorPersistencia):
        repo.guardar_feria(1, feria, (("A", None),))
    assert conexion.execute("SELECT COUNT(*) FROM feria").fetchone()[0] == antes
    assert conexion.execute("SELECT COUNT(*) FROM rubrica").fetchone()[0] == 1
