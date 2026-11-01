"""HU-009 · ``GET /api/resultados`` contra la base temporal.

Datos de partida (app/datos_demo.sql): el estudiante 2 es integrante del Equipo Demo, que
inscribió el proyecto 1; el docente 1 tiene asignada su evaluación (PENDIENTE).
"""

import pytest

from app.dominio.modelos import EstadoEvaluacion, ResultadoEvaluacion
from app.repositorios.sqlite_repositorios import SqliteResultadoRepositorio

URL = "/api/resultados?estudiante_id=2"
NOTAS = {"1": 4, "2": 3, "3": 5}


def calificar(cliente, confirmar):
    """El docente 1 califica el proyecto 1 con retroalimentación."""
    return cliente.put("/api/proyectos/1/evaluacion", json={
        "evaluador_id": 1, "notas": NOTAS, "confirmar": confirmar,
        "retroalimentacion": "Buen trabajo; falta documentar las pruebas."})


def evaluacion_del_proyecto(cliente):
    """Única evaluación del proyecto 1 tal como la ve el estudiante."""
    proyecto = cliente.get(URL).get_json()[0]
    assert (proyecto["proyecto"], proyecto["equipo"]) == ("Proyecto Demo", "Equipo Demo")
    return proyecto["evaluaciones"][0]


def test_rn007_oculta_puntaje_y_retroalimentacion_hasta_confirmar(cliente):
    """Criterios 1 y 2: pendiente y borrador ocultan; confirmada muestra 3.9 y el texto."""
    pendiente = evaluacion_del_proyecto(cliente)
    assert (pendiente["estado"], pendiente["puntaje_final"],
            pendiente["retroalimentacion"]) == ("PENDIENTE", None, None)

    assert calificar(cliente, confirmar=False).status_code == 200
    borrador = evaluacion_del_proyecto(cliente)
    assert (borrador["estado"], borrador["puntaje_final"],
            borrador["retroalimentacion"]) == ("BORRADOR", None, None)

    assert calificar(cliente, confirmar=True).status_code == 200
    confirmada = evaluacion_del_proyecto(cliente)
    assert confirmada["estado"] == "CONFIRMADA"
    assert confirmada["puntaje_final"] == 3.9
    assert confirmada["retroalimentacion"] == "Buen trabajo; falta documentar las pruebas."
    assert confirmada["evaluador"] == "Docente Evaluador"
    assert confirmada["fecha_confirmacion"] is not None          # RNF-06


def test_el_evaluador_ve_su_propia_retroalimentacion_en_borrador(cliente):
    """El listado del evaluador sí trae el texto del borrador, para seguir editándolo."""
    calificar(cliente, confirmar=False)
    propia = cliente.get("/api/evaluaciones?evaluador_id=1").get_json()[0]
    assert propia["retroalimentacion"] == "Buen trabajo; falta documentar las pruebas."


def test_el_evaluador_recupera_las_notas_del_borrador(cliente):
    """Antes de calificar no hay notas; tras el borrador vuelven por criterio para llenar el
    formulario."""
    url = "/api/evaluaciones?evaluador_id=1"
    assert cliente.get(url).get_json()[0]["notas"] == {}
    calificar(cliente, confirmar=False)
    assert cliente.get(url).get_json()[0]["notas"] == {"1": 4.0, "2": 3.0, "3": 5.0}


def test_retroalimentacion_que_no_es_texto_responde_400(cliente):
    """HU-007 rechaza ``retroalimentacion`` numérica y no guarda nada."""
    respuesta = cliente.put("/api/proyectos/1/evaluacion", json={
        "evaluador_id": 1, "notas": NOTAS, "retroalimentacion": 5})
    assert respuesta.status_code == 400
    assert evaluacion_del_proyecto(cliente)["estado"] == "PENDIENTE"


@pytest.mark.parametrize("url, estado, codigo", [
    pytest.param("/api/resultados", 400, "dato_invalido", id="sin-parametro"),
    pytest.param("/api/resultados?estudiante_id=abc", 400, "dato_invalido", id="texto"),
    pytest.param("/api/resultados?estudiante_id=99", 404, "usuario_no_encontrado",
                 id="no-existe"),
    pytest.param("/api/resultados?estudiante_id=1", 422, "usuario_no_estudiante",
                 id="docente"),
])
def test_solicitudes_rechazadas(cliente, url, estado, codigo):
    """D1, D2 y D3 a través de HTTP."""
    respuesta = cliente.get(url)
    assert respuesta.status_code == estado
    assert respuesta.get_json()["codigo"] == codigo


def test_repositorio_incluye_proyectos_sin_evaluadores(conexion):
    """Un proyecto inscrito sin evaluador aparece con la lista de evaluaciones vacía."""
    conexion.execute(
        "INSERT INTO proyecto (id, equipo_id, feria_id, nombre, nombre_normalizado, "
        "modalidad, fecha_inscripcion) VALUES (2, 1, 1, 'Segundo', 'segundo', 'PA', "
        "'2026-10-20')")
    repo = SqliteResultadoRepositorio(conexion)
    primero, segundo = repo.resultados_de_estudiante(2)
    assert primero.evaluaciones == (ResultadoEvaluacion(
        1, "Docente Evaluador", EstadoEvaluacion.PENDIENTE, None, "", None),)
    assert (segundo.proyecto, segundo.evaluaciones) == ("Segundo", ())
    assert repo.rol_de_usuario(2) == "ESTUDIANTE"
    assert repo.rol_de_usuario(99) is None
