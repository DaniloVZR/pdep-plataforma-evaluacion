"""Flujo completo controlador → servicio → repositorio → SQLite con el cliente de Flask.

Una prueba de éxito y una de error por historia, para comprobar que el
manejador global traduce cada excepción al código HTTP correcto.
"""


def test_hu003_registro_exitoso_y_duplicado(cliente):
    """201 al registrar y 409 al repetir el correo con otras mayúsculas."""
    cuerpo = {"nombres": "Ana", "correo": "ana@pascualbravo.edu.co", "rol": "ESTUDIANTE",
              "programa_id": 1, "asignatura_ids": [1]}
    respuesta = cliente.post("/api/usuarios", json=cuerpo)
    assert respuesta.status_code == 201
    assert respuesta.get_json()["correo"] == "ana@pascualbravo.edu.co"
    repetido = cliente.post("/api/usuarios", json={**cuerpo, "correo": "ANA@pascualbravo.edu.co"})
    assert repetido.status_code == 409
    assert repetido.get_json()["codigo"] == "correo_duplicado"


def test_hu003_cuerpo_que_no_es_json(cliente):
    """``get_json(silent=True)`` devuelve None y el validador responde 400."""
    respuesta = cliente.post("/api/usuarios", data="no es json", content_type="text/plain")
    assert respuesta.status_code == 400
    assert respuesta.get_json()["codigo"] == "dato_invalido"


def test_hu005_inscripcion_exitosa_y_asignatura_que_no_participa(cliente):
    """201 con asignaturas de la feria y 422 con la asignatura 3, que no participa."""
    cuerpo = {"equipo_id": 1, "feria_id": 1, "nombre": "Robot", "modalidad": "PIA",
              "asignatura_ids": [1, 2]}
    assert cliente.post("/api/proyectos", json=cuerpo).status_code == 201
    respuesta = cliente.post("/api/proyectos", json={**cuerpo, "nombre": "Otro",
                                                     "asignatura_ids": [1, 3]})
    assert respuesta.status_code == 422
    assert respuesta.get_json()["codigo"] == "asignatura_no_participante"


def test_hu007_borrador_confirmacion_y_bloqueo(cliente):
    """Borrador sin puntaje visible, confirmación con 3.9 y 409 al intentar cambiarla."""
    url = "/api/proyectos/1/evaluacion"
    notas = {"1": 4.0, "2": 3.0, "3": 5.0}
    borrador = cliente.put(url, json={"evaluador_id": 1, "notas": notas})
    assert borrador.get_json()["estado"] == "BORRADOR"
    assert borrador.get_json()["puntaje_final"] is None
    confirmada = cliente.put(url, json={"evaluador_id": 1, "notas": notas, "confirmar": True})
    assert confirmada.get_json()["puntaje_final"] == 3.9
    assert confirmada.get_json()["fecha_confirmacion"] is not None
    assert cliente.put(url, json={"evaluador_id": 1, "notas": notas}).status_code == 409


def test_hu007_evaluador_no_asignado_y_nan(cliente):
    """403 para un evaluador sin asignación y 422 para una nota NaN en el JSON."""
    url = "/api/proyectos/1/evaluacion"
    otro = cliente.put(url, json={"evaluador_id": 2, "notas": {"1": 4}})
    assert otro.status_code == 403
    nan = cliente.put(url, data='{"evaluador_id": 1, "notas": {"1": NaN, "2": 3, "3": 4}}',
                      content_type="application/json")
    assert nan.status_code == 422
    assert nan.get_json()["codigo"] == "tipo_nota_invalido"
