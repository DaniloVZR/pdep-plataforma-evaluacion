"""HU-008 · REQ-16 · RN006: el resultado calculado no se puede modificar manualmente.

Dos barreras: la API rechaza un puntaje enviado en la solicitud (PDEP-50) y la base de
datos rechaza cualquier cambio a una evaluación ya confirmada (PDEP-51).
"""

import sqlite3

import pytest

URL = "/api/proyectos/1/evaluacion"
NOTAS = {"1": 4.0, "2": 3.0, "3": 5.0}     # 4.0×0.5 + 3.0×0.3 + 5.0×0.2 = 3.9


def confirmar(cliente):
    """Confirma la evaluación 1 del proyecto 1 (datos de demostración) y la devuelve."""
    respuesta = cliente.put(URL, json={"evaluador_id": 1, "notas": NOTAS, "confirmar": True})
    assert respuesta.status_code == 200
    return respuesta.get_json()


def fila_evaluacion(conexion):
    """Estado y puntaje guardados de la evaluación 1."""
    return tuple(conexion.execute(
        "SELECT estado, puntaje_final FROM evaluacion WHERE id = 1").fetchone())


# --- PDEP-50: la API ---------------------------------------------------------------

@pytest.mark.parametrize("campo", ["puntaje_final", "puntaje"])
def test_api_rechaza_puntaje_enviado_y_no_guarda_nada(cliente, conexion, campo):
    """400 ``puntaje_no_editable``; la evaluación sigue PENDIENTE y sin puntaje."""
    respuesta = cliente.put(URL, json={"evaluador_id": 1, "notas": NOTAS,
                                       "confirmar": True, campo: 5.0})
    assert respuesta.status_code == 400
    assert respuesta.get_json()["codigo"] == "puntaje_no_editable"
    assert fila_evaluacion(conexion) == ("PENDIENTE", None)


def test_api_calcula_el_puntaje_sin_que_nadie_lo_envie(cliente, conexion):
    """Criterio 1 de HU-008: con solo las notas, el sistema guarda 3.9."""
    assert confirmar(cliente)["puntaje_final"] == 3.9
    assert fila_evaluacion(conexion) == ("CONFIRMADA", 3.9)


# --- PDEP-51: la base de datos -----------------------------------------------------

@pytest.mark.parametrize("sentencia", [
    "UPDATE evaluacion SET puntaje_final = 5.0 WHERE id = 1",
    "UPDATE evaluacion SET estado = 'BORRADOR' WHERE id = 1",
    "UPDATE evaluacion SET fecha_confirmacion = NULL WHERE id = 1",
    "DELETE FROM evaluacion WHERE id = 1",
    "UPDATE calificacion_criterio SET nota = 5.0 WHERE evaluacion_id = 1",
    "DELETE FROM calificacion_criterio WHERE evaluacion_id = 1",
])
def test_bd_rechaza_cambios_a_una_evaluacion_confirmada(cliente, conexion, sentencia):
    """Aunque se use SQL directo, el puntaje y las notas confirmadas no cambian."""
    confirmar(cliente)
    with pytest.raises(sqlite3.IntegrityError, match="evaluacion_confirmada"):
        conexion.execute(sentencia)
    assert fila_evaluacion(conexion) == ("CONFIRMADA", 3.9)
    assert conexion.execute(
        "SELECT COUNT(*) FROM calificacion_criterio WHERE evaluacion_id = 1").fetchone()[0] == 3


def test_bd_permite_corregir_un_borrador(cliente, conexion):
    """Mientras no esté confirmada, el evaluador puede volver a guardar sus notas."""
    cliente.put(URL, json={"evaluador_id": 1, "notas": NOTAS})
    conexion.execute("UPDATE calificacion_criterio SET nota = 5.0 WHERE evaluacion_id = 1")
    conexion.execute("UPDATE evaluacion SET retroalimentacion = 'Ajuste' WHERE id = 1")
    conexion.commit()
    assert fila_evaluacion(conexion)[0] == "BORRADOR"
    assert confirmar(cliente)["estado"] == "CONFIRMADA"
