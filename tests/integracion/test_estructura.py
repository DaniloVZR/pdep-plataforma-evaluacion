"""HU-001 · Endpoints de la estructura académica contra la base temporal.

Datos de partida (app/datos_demo.sql): institución 1 con dominio pascualbravo.edu.co,
facultad 1 (Ingeniería), departamento 1 (Ciencias Básicas) y programa 1 (TDS, facultad 1).
"""

import time

from app.db import abrir_conexion
from app.dominio.modelos import Facultad
from app.repositorios.sqlite_repositorios import SqliteEstructuraRepositorio


def test_registrar_institucion_y_listarla_con_su_dominio(cliente):
    """201 y la institución aparece con contacto y dominio; el NIT repetido da 409."""
    cuerpo = {"nombre": "Instituto Tecnológico Metropolitano", "nit": "800214750",
              "correo_contacto": "info@itm.edu.co", "telefono": "123", "dominio": "itm.edu.co"}
    respuesta = cliente.post("/api/instituciones", json=cuerpo)
    assert respuesta.status_code == 201
    creada = respuesta.get_json()
    listado = cliente.get("/api/instituciones").get_json()
    itm = next(i for i in listado if i["id"] == creada["id"])
    assert itm["dominios"] == ["itm.edu.co"]
    assert itm["correo_contacto"] == "info@itm.edu.co"
    repetida = cliente.post("/api/instituciones", json={**cuerpo, "dominio": "otro.edu.co"})
    assert repetida.status_code == 409
    assert repetida.get_json()["codigo"] == "institucion_duplicada"


def test_dominio_repetido_no_deja_la_institucion_a_medias(cliente, ruta_bd):
    """Si el dominio ya existe, la transacción deshace también la institución."""
    respuesta = cliente.post("/api/instituciones", json={
        "nombre": "Copia", "nit": "111", "dominio": "pascualbravo.edu.co"})
    assert respuesta.status_code == 409
    conexion = abrir_conexion(ruta_bd)
    assert conexion.execute("SELECT COUNT(*) FROM institucion").fetchone()[0] == 1
    conexion.close()


def test_institucion_sin_nombre_responde_400(cliente):
    """Criterio de aceptación 1."""
    respuesta = cliente.post("/api/instituciones", json={"nit": "800"})
    assert respuesta.status_code == 400
    assert "nombre de la institución" in respuesta.get_json()["mensaje"]


def test_facultad_sin_nombre_responde_400(cliente):
    """Criterio de aceptación 1."""
    respuesta = cliente.post("/api/facultades", json={"institucion_id": 1, "nombre": ""})
    assert respuesta.status_code == 400
    assert "nombre de la facultad" in respuesta.get_json()["mensaje"]


def test_facultad_nueva_aparece_en_el_listado_en_menos_de_2_segundos(cliente):
    """Criterio de aceptación 2: registrar y volver a listar tarda menos de 2 s."""
    inicio = time.perf_counter()
    creada = cliente.post("/api/facultades", json={"institucion_id": 1, "nombre": "Artes"})
    listado = cliente.get("/api/facultades?institucion_id=1").get_json()
    assert time.perf_counter() - inicio < 2
    assert creada.status_code == 201
    assert "Artes" in [f["nombre"] for f in listado]


def test_facultad_repetida_sin_distinguir_mayusculas_y_de_institucion_inexistente(cliente):
    """409 con el mismo nombre en otras mayúsculas y 404 con la institución 99."""
    repetida = cliente.post("/api/facultades", json={"institucion_id": 1,
                                                      "nombre": "facultad de ingeniería"})
    assert repetida.status_code == 409
    assert repetida.get_json()["codigo"] == "facultad_duplicada"
    otra = cliente.post("/api/facultades", json={"institucion_id": 99, "nombre": "Artes"})
    assert otra.status_code == 404
    assert otra.get_json()["codigo"] == "institucion_no_encontrada"


def test_departamento_registro_y_listado(cliente):
    """201 al crear; el listado sin filtro y con filtro lo incluye; repetido da 409."""
    cuerpo = {"institucion_id": 1, "nombre": "Humanidades"}
    assert cliente.post("/api/departamentos", json=cuerpo).status_code == 201
    assert cliente.post("/api/departamentos", json=cuerpo).status_code == 409
    nombres = [d["nombre"] for d in cliente.get("/api/departamentos").get_json()]
    assert nombres == ["Departamento de Ciencias Básicas", "Humanidades"]
    assert len(cliente.get("/api/departamentos?institucion_id=1").get_json()) == 2


def test_filtro_de_institucion_invalido_responde_400(cliente):
    """``institucion_id`` debe ser un entero mayor que 0."""
    assert cliente.get("/api/facultades?institucion_id=abc").status_code == 400


def test_programa_registro_listado_y_errores(cliente):
    """201 y aparece en /api/programas con su facultad; 409 código repetido; 422 otra
    institución."""
    cuerpo = {"institucion_id": 1, "codigo": "isw", "nombre": "Ingeniería de Software",
              "facultad_id": 1}
    creado = cliente.post("/api/programas", json=cuerpo)
    assert creado.status_code == 201
    assert creado.get_json()["codigo"] == "ISW"
    programa = next(p for p in cliente.get("/api/programas").get_json() if p["codigo"] == "ISW")
    assert (programa["facultad_id"], programa["departamento_id"]) == (1, None)
    assert programa["asignaturas"] == []
    assert cliente.post("/api/programas", json=cuerpo).status_code == 409
    cliente.post("/api/instituciones", json={"nombre": "ITM", "nit": "800"})
    otra = cliente.post("/api/programas", json={**cuerpo, "codigo": "X", "institucion_id": 2})
    assert otra.status_code == 422
    assert otra.get_json()["codigo"] == "estructura_inconsistente"


def test_programa_sin_facultad_ni_departamento_responde_400(cliente):
    """REQ-3."""
    respuesta = cliente.post("/api/programas", json={"institucion_id": 1, "codigo": "X",
                                                     "nombre": "X"})
    assert respuesta.status_code == 400


def test_repositorio_devuelve_institucion_de_cada_unidad(conexion):
    """``institucion_de_*`` devuelve la institución dueña o ``None``."""
    repo = SqliteEstructuraRepositorio(conexion)
    assert repo.institucion_de_facultad(1) == 1
    assert repo.institucion_de_departamento(1) == 1
    assert repo.institucion_de_facultad(99) is None
    assert repo.guardar_facultad(Facultad(None, 1, "Artes")).id == 2
