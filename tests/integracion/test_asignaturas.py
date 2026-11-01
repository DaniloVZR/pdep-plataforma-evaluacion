"""HU-002 · Endpoints de asignaturas contra la base temporal.

Datos de partida (app/datos_demo.sql): programa 1 (TDS) con las asignaturas IS2, BD2 y RD2.
"""

import pytest

from app.dominio.errores import ConflictoUnicidadError
from app.dominio.modelos import Asignatura
from app.repositorios.sqlite_repositorios import SqliteRegistroAsignaturaRepositorio

NUEVA = {"programa_id": 1, "codigo": "IS3", "nombre": "Ingeniería de Software III",
         "semestre": 6}


def test_registrar_asignatura_y_verla_en_el_listado_del_programa(cliente):
    """Criterios 1 y 2: 201 y la asignatura aparece en el listado del programa elegido."""
    respuesta = cliente.post("/api/asignaturas", json=NUEVA)
    assert respuesta.status_code == 201
    creada = respuesta.get_json()
    assert creada["programa_id"] == 1
    listado = cliente.get("/api/asignaturas?programa_id=1").get_json()
    fila = next(a for a in listado if a["id"] == creada["id"])
    assert fila["codigo"] == "IS3"
    assert fila["programa"] == "Tecnología en Desarrollo de Software"


def test_listado_sin_filtro_y_ordenado_por_semestre(cliente):
    """Sin ``programa_id`` devuelve todas; las del semestre 5 van antes que la del 6."""
    cliente.post("/api/asignaturas", json=NUEVA)
    listado = cliente.get("/api/asignaturas").get_json()
    assert [a["codigo"] for a in listado] == ["BD2", "IS2", "RD2", "IS3"]


def test_programa_inexistente(cliente):
    """404 al registrar y al listar con el programa 99."""
    respuesta = cliente.post("/api/asignaturas", json={**NUEVA, "programa_id": 99})
    assert respuesta.status_code == 404
    assert respuesta.get_json()["codigo"] == "programa_no_encontrado"
    assert cliente.get("/api/asignaturas?programa_id=99").status_code == 404


def test_codigo_repetido_responde_409(cliente):
    """IS2 ya existe en los datos de demostración (en minúsculas también choca)."""
    respuesta = cliente.post("/api/asignaturas", json={**NUEVA, "codigo": "is2"})
    assert respuesta.status_code == 409
    assert respuesta.get_json()["codigo"] == "asignatura_duplicada"


@pytest.mark.parametrize("cuerpo, mensaje", [
    pytest.param({**NUEVA, "programa_id": None}, "programa académico", id="sin-programa"),
    pytest.param({**NUEVA, "nombre": ""}, "nombre", id="sin-nombre"),
])
def test_datos_incompletos_responden_400(cliente, cuerpo, mensaje):
    """Falta el programa o el nombre."""
    respuesta = cliente.post("/api/asignaturas", json=cuerpo)
    assert respuesta.status_code == 400
    assert mensaje in respuesta.get_json()["mensaje"]


@pytest.mark.parametrize("valor", ["0", "abc", "-1"])
def test_listado_con_programa_id_invalido_responde_400(cliente, valor):
    """El filtro debe ser un entero mayor que 0."""
    assert cliente.get(f"/api/asignaturas?programa_id={valor}").status_code == 400


def test_repositorio_rechaza_el_codigo_duplicado(conexion):
    """La restricción UNIQUE de ``asignatura.codigo`` llega como ``ConflictoUnicidadError``."""
    repo = SqliteRegistroAsignaturaRepositorio(conexion)
    guardada = repo.guardar(Asignatura(None, 1, "IS3", "Ingeniería de Software III", 6))
    assert guardada.id is not None
    with pytest.raises(ConflictoUnicidadError):
        repo.guardar(Asignatura(None, 1, "IS3", "Otra", 6))
