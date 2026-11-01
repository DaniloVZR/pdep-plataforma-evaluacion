"""HU-006 · Asignación de evaluadores y carga por evaluador contra la base temporal.

Datos de partida (app/datos_demo.sql): proyecto 1 con el docente 1 ya asignado (evaluación 1
PENDIENTE) y el usuario 2, que es estudiante.
"""

import pytest

from app.db import abrir_conexion
from app.dominio.errores import ConflictoUnicidadError
from app.repositorios.sqlite_repositorios import SqliteAsignacionRepositorio


@pytest.fixture(name="docente_3")
def fixture_docente_3(ruta_bd):
    """Agrega un segundo docente (id 3) para tener a quién asignar."""
    conexion = abrir_conexion(ruta_bd)
    with conexion:
        conexion.execute("INSERT INTO usuario (id, nombres, correo, rol, programa_id) VALUES "
                         "(3, 'Docente Dos', 'docente2@pascualbravo.edu.co', 'DOCENTE', 1)")
    conexion.close()
    return 3


def test_asignar_un_evaluador_nuevo(cliente, docente_3):
    """201: el docente 3 queda con una evaluación PENDIENTE del proyecto 1."""
    respuesta = cliente.post("/api/proyectos/1/evaluadores", json={"evaluador_ids": [docente_3]})
    assert respuesta.status_code == 201
    assert respuesta.get_json()["asignados"][0]["evaluador_id"] == 3
    evaluaciones = cliente.get("/api/evaluaciones?evaluador_id=3").get_json()
    assert [(e["proyecto_id"], e["estado"]) for e in evaluaciones] == [(1, "PENDIENTE")]


def test_no_se_asigna_dos_veces_el_mismo_evaluador(cliente, docente_3):
    """Criterio de aceptación 1 (REQ-12): 409 y el docente 3 tampoco queda asignado."""
    respuesta = cliente.post("/api/proyectos/1/evaluadores",
                             json={"evaluador_ids": [docente_3, 1]})
    assert respuesta.status_code == 409
    assert respuesta.get_json()["codigo"] == "evaluador_ya_asignado"
    assert cliente.get("/api/evaluaciones?evaluador_id=3").get_json() == []


def test_errores_de_la_asignacion(cliente):
    """404 proyecto, 404 evaluador, 422 estudiante y 400 lista vacía."""
    url = "/api/proyectos/1/evaluadores"
    casos = [
        ("/api/proyectos/99/evaluadores", {"evaluador_ids": [1]}, 404, "proyecto_no_encontrado"),
        (url, {"evaluador_ids": [99]}, 404, "evaluador_no_encontrado"),
        (url, {"evaluador_ids": [2]}, 422, "usuario_no_docente"),
        (url, {"evaluador_ids": []}, 400, "dato_invalido"),
    ]
    for ruta, cuerpo, estado, codigo in casos:
        respuesta = cliente.post(ruta, json=cuerpo)
        assert (respuesta.status_code, respuesta.get_json()["codigo"]) == (estado, codigo)


def test_carga_por_evaluador(cliente, docente_3):
    """Criterio de aceptación 2: el docente 1 tiene 1 proyecto y el 3 aparece con 0."""
    carga = {c["id"]: c for c in cliente.get("/api/evaluadores/carga").get_json()}
    assert set(carga) == {1, 3}
    assert (carga[1]["asignados"], carga[1]["pendientes"]) == (1, 1)
    assert (carga[3]["asignados"], carga[3]["confirmadas"]) == (0, 0)
    cliente.put("/api/proyectos/1/evaluacion", json={
        "evaluador_id": 1, "notas": {"1": 4, "2": 3, "3": 5}, "confirmar": True})
    cliente.post("/api/proyectos/1/evaluadores", json={"evaluador_ids": [docente_3]})
    carga = {c["id"]: c for c in cliente.get("/api/evaluadores/carga").get_json()}
    assert (carga[1]["confirmadas"], carga[1]["pendientes"]) == (1, 0)
    assert carga[3]["asignados"] == 1


def test_el_listado_de_proyectos_muestra_sus_evaluadores(cliente):
    """El proyecto 1 lista al docente 1 como evaluador."""
    proyecto = cliente.get("/api/proyectos").get_json()[0]
    assert proyecto["evaluadores"] == [{"id": 1, "nombres": "Docente Evaluador"}]


def test_repositorio_deshace_toda_la_asignacion_si_una_falla(conexion, docente_3):
    """Si el segundo INSERT viola UNIQUE, el primero tampoco queda guardado."""
    repo = SqliteAsignacionRepositorio(conexion)
    with pytest.raises(ConflictoUnicidadError):
        repo.asignar(1, (docente_3, 1))
    assert repo.evaluadores_asignados(1) == frozenset({1})
