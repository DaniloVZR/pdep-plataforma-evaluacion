"""Endpoints de consulta (PDEP-35) contra la base temporal con los datos de demostración.

Datos de partida (app/datos_demo.sql): programa 1 con 3 asignaturas, 2 usuarios
(1 docente evaluador, 1 estudiante), equipo 1, feria 1 con asignaturas 1 y 2,
rúbrica de 3 criterios (0.5, 0.3, 0.2), proyecto 1 y su evaluación 1 PENDIENTE.
"""

import pytest

from app.db import abrir_conexion


def test_programas_con_sus_asignaturas(cliente):
    """El programa trae sus 3 asignaturas anidadas."""
    programas = cliente.get("/api/programas").get_json()
    assert len(programas) == 1
    assert programas[0]["codigo"] == "TDS"
    assert {a["codigo"] for a in programas[0]["asignaturas"]} == {"IS2", "BD2", "RD2"}


def test_usuarios_sin_filtro_y_filtrados_por_rol(cliente):
    """Sin filtro devuelve los 2 usuarios; el rol se acepta en minúsculas."""
    assert len(cliente.get("/api/usuarios").get_json()) == 2
    docentes = cliente.get("/api/usuarios?rol=docente").get_json()
    assert [d["id"] for d in docentes] == [1]
    assert docentes[0]["rol"] == "DOCENTE"


def test_usuarios_con_rol_inexistente_responde_400(cliente):
    """Un rol fuera de ESTUDIANTE/DOCENTE es un dato inválido."""
    respuesta = cliente.get("/api/usuarios?rol=ADMIN")
    assert respuesta.status_code == 400
    assert respuesta.get_json()["codigo"] == "dato_invalido"


def test_equipos_con_sus_integrantes(cliente):
    """El equipo 1 tiene como integrante al estudiante 2."""
    equipos = cliente.get("/api/equipos").get_json()
    assert equipos == [{"id": 1, "nombre": "Equipo Demo",
                        "integrantes": [{"id": 2, "nombres": "Estudiante Demo"}]}]


def test_ferias_con_fechas_y_asignaturas_participantes(cliente):
    """La feria 1 lista solo las asignaturas que participan (1 y 2, no la 3)."""
    feria = cliente.get("/api/ferias").get_json()[0]
    assert (feria["fecha_inicio"], feria["fecha_fin"]) == ("2026-01-01", "2026-12-31")
    assert sorted(a["id"] for a in feria["asignaturas"]) == [1, 2]


def test_rubrica_de_la_feria(cliente):
    """Escala 1.0 a 5.0 y 3 criterios cuyos pesos suman 1."""
    rubrica = cliente.get("/api/ferias/1/rubrica").get_json()
    assert (rubrica["nota_minima"], rubrica["nota_maxima"]) == (1.0, 5.0)
    assert [c["peso"] for c in rubrica["criterios"]] == [0.5, 0.3, 0.2]


def test_rubrica_de_feria_inexistente_responde_404(cliente):
    """La feria 99 no existe."""
    respuesta = cliente.get("/api/ferias/99/rubrica")
    assert respuesta.status_code == 404
    assert respuesta.get_json()["codigo"] == "feria_no_encontrada"


def test_rubrica_de_feria_sin_rubrica_responde_422(cliente, ruta_bd):
    """Una feria que existe pero no tiene rúbrica responde como en HU-007 (RN005)."""
    conexion = abrir_conexion(ruta_bd)
    with conexion:
        conexion.execute("INSERT INTO feria (id, institucion_id, nombre, fecha_inicio, fecha_fin)"
                         " VALUES (2, 1, 'Feria sin rúbrica', '2026-11-01', '2026-11-30')")
    conexion.close()
    respuesta = cliente.get("/api/ferias/2/rubrica")
    assert respuesta.status_code == 422
    assert respuesta.get_json()["codigo"] == "rubrica_no_encontrada"


def test_proyectos_sin_filtro_y_por_feria(cliente):
    """El proyecto 1 aparece con su equipo y sus asignaturas, con o sin filtro."""
    todos = cliente.get("/api/proyectos").get_json()
    assert todos[0]["equipo"] == "Equipo Demo"
    assert todos[0]["asignatura_ids"] == [1]
    assert cliente.get("/api/proyectos?feria_id=1").get_json() == todos


@pytest.mark.parametrize("valor", ["abc", "0", "-1", "1.5"])
def test_proyectos_con_feria_id_invalido_responde_400(cliente, valor):
    """``feria_id`` debe ser un entero mayor que 0."""
    assert cliente.get(f"/api/proyectos?feria_id={valor}").status_code == 400


def test_evaluaciones_ocultan_el_puntaje_hasta_confirmar(cliente):
    """PENDIENTE sin puntaje; tras confirmar con notas 4, 3 y 5 muestra 3.9 (RN007)."""
    url = "/api/evaluaciones?evaluador_id=1"
    pendiente = cliente.get(url).get_json()[0]
    assert (pendiente["estado"], pendiente["puntaje_final"]) == ("PENDIENTE", None)
    cliente.put("/api/proyectos/1/evaluacion", json={
        "evaluador_id": 1, "notas": {"1": 4, "2": 3, "3": 5}, "confirmar": False})
    assert cliente.get(url).get_json()[0]["puntaje_final"] is None
    cliente.put("/api/proyectos/1/evaluacion", json={
        "evaluador_id": 1, "notas": {"1": 4, "2": 3, "3": 5}, "confirmar": True})
    confirmada = cliente.get(url).get_json()[0]
    assert (confirmada["estado"], confirmada["puntaje_final"]) == ("CONFIRMADA", 3.9)


def test_evaluaciones_de_evaluador_sin_asignaciones(cliente):
    """El estudiante 2 no tiene evaluaciones asignadas: lista vacía."""
    assert cliente.get("/api/evaluaciones?evaluador_id=2").get_json() == []


def test_evaluaciones_sin_evaluador_id_responde_400(cliente):
    """``evaluador_id`` es obligatorio."""
    respuesta = cliente.get("/api/evaluaciones")
    assert respuesta.status_code == 400
    assert "evaluador_id" in respuesta.get_json()["mensaje"]
