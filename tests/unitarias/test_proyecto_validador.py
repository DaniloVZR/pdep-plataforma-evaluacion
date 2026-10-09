"""HU-005 · Condiciones internas de ``validar_datos_inscripcion``."""

import pytest

from app.dominio.errores import DatoInvalidoError
from app.validadores.proyecto_validador import normalizar_nombre, validar_datos_inscripcion

PA = {"equipo_id": 1, "feria_id": 1, "nombre": "App", "modalidad": "PA", "asignatura_ids": [1]}
PIA = {**PA, "modalidad": "PIA", "asignatura_ids": [1, 2]}


@pytest.mark.parametrize("datos", [
    pytest.param(None, id="cuerpo-nulo"),
    pytest.param({**PA, "equipo_id": None}, id="equipo-nulo"),
    pytest.param({**PA, "feria_id": "1"}, id="feria-texto"),
    pytest.param({**PA, "nombre": " "}, id="nombre-vacio"),
    pytest.param({**PA, "modalidad": "pa"}, id="modalidad-minuscula"),
    pytest.param({**PA, "modalidad": None}, id="modalidad-nula"),
    pytest.param({**PA, "asignatura_ids": []}, id="sin-asignaturas"),
    pytest.param({**PA, "asignatura_ids": None}, id="asignaturas-nulas"),
    pytest.param({**PA, "asignatura_ids": [1, 2]}, id="PA-con-dos-asignaturas"),
    pytest.param({**PIA, "asignatura_ids": [1]}, id="PIA-con-una-asignatura"),
    pytest.param({**PIA, "asignatura_ids": [1, 1]}, id="PIA-con-asignatura-repetida"),
])
def test_solicitudes_invalidas(datos):
    """Cada condición falsa de D1 lanza ``DatoInvalidoError`` (incluye RN009)."""
    with pytest.raises(DatoInvalidoError):
        validar_datos_inscripcion(datos)


@pytest.mark.parametrize("datos", [pytest.param(PA, id="PA"), pytest.param(PIA, id="PIA")])
def test_solicitudes_validas(datos):
    """PA con una asignatura y PIA con dos pasan."""
    validar_datos_inscripcion(datos)


def test_normalizar_nombre_detecta_el_mismo_proyecto():
    """Mayúsculas y espacios extra no crean un proyecto distinto (RN002)."""
    assert normalizar_nombre("  Robot   CLASIFICADOR ") == normalizar_nombre("robot clasificador")
