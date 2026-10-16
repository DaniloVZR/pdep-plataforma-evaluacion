"""HU-001 · Condiciones de los validadores de institución, facultad/departamento y programa."""

import pytest

from app.dominio.errores import DatoInvalidoError
from app.validadores.estructura_validador import (
    dominio_valido,
    limpiar_texto,
    validar_datos_institucion,
    validar_datos_programa,
    validar_datos_unidad,
)

INSTITUCION = {"nombre": "Pascual Bravo", "nit": "890980153",
               "correo_contacto": "info@pascualbravo.edu.co", "telefono": "123",
               "dominio": "pascualbravo.edu.co"}
PROGRAMA = {"institucion_id": 1, "codigo": "TDS", "nombre": "Desarrollo", "facultad_id": 1}


def sin(datos, campo):
    """Copia de ``datos`` sin un campo."""
    return {clave: valor for clave, valor in datos.items() if clave != campo}


@pytest.mark.parametrize("datos, mensaje", [
    pytest.param(None, "objeto JSON", id="cuerpo-nulo"),
    pytest.param(sin(INSTITUCION, "nombre"), "nombre de la institución", id="sin-nombre"),
    pytest.param({**INSTITUCION, "nombre": "  "}, "nombre de la institución",
                 id="nombre-vacio"),
    pytest.param(sin(INSTITUCION, "nit"), "NIT", id="sin-nit"),
    pytest.param({**INSTITUCION, "telefono": 3001234567}, "telefono", id="telefono-numero"),
    pytest.param({**INSTITUCION, "dominio": "ana@pascualbravo.edu.co"}, "dominio",
                 id="dominio-con-arroba"),
])
def test_institucion_invalida(datos, mensaje):
    """Criterio de aceptación: se rechaza si falta el nombre de la institución."""
    with pytest.raises(DatoInvalidoError, match=mensaje):
        validar_datos_institucion(datos)


@pytest.mark.parametrize("datos", [
    pytest.param(INSTITUCION, id="completa"),
    pytest.param({"nombre": "ITM", "nit": "800"}, id="solo-obligatorios"),
    pytest.param({**INSTITUCION, "dominio": "  "}, id="dominio-en-blanco"),
])
def test_institucion_valida(datos):
    """Contacto y dominio son opcionales."""
    validar_datos_institucion(datos)


@pytest.mark.parametrize("datos, mensaje", [
    pytest.param([], "objeto JSON", id="cuerpo-lista"),
    pytest.param({"nombre": "Ingeniería"}, "institucion_id", id="sin-institucion"),
    pytest.param({"institucion_id": True, "nombre": "Ingeniería"}, "institucion_id",
                 id="institucion-booleano"),
    pytest.param({"institucion_id": 1}, "nombre de la facultad", id="sin-nombre"),
    pytest.param({"institucion_id": 1, "nombre": ""}, "nombre de la facultad",
                 id="nombre-vacio"),
])
def test_facultad_invalida(datos, mensaje):
    """Criterio de aceptación: se rechaza si falta el nombre de la facultad."""
    with pytest.raises(DatoInvalidoError, match=mensaje):
        validar_datos_unidad(datos, "facultad")


def test_unidad_valida_y_mensaje_del_departamento():
    """El mismo validador sirve para el departamento, con su propio mensaje."""
    validar_datos_unidad({"institucion_id": 1, "nombre": "Ciencias"}, "departamento")
    with pytest.raises(DatoInvalidoError, match="nombre del departamento"):
        validar_datos_unidad({"institucion_id": 1}, "departamento")


@pytest.mark.parametrize("datos, mensaje", [
    pytest.param("TDS", "objeto JSON", id="cuerpo-texto"),
    pytest.param(sin(PROGRAMA, "institucion_id"), "institucion_id", id="sin-institucion"),
    pytest.param(sin(PROGRAMA, "codigo"), "código", id="sin-codigo"),
    pytest.param(sin(PROGRAMA, "nombre"), "nombre del programa", id="sin-nombre"),
    pytest.param({**PROGRAMA, "facultad_id": 0}, "facultad_id", id="facultad-cero"),
    pytest.param({**PROGRAMA, "departamento_id": "2"}, "departamento_id",
                 id="departamento-texto"),
    pytest.param(sin(PROGRAMA, "facultad_id"), "facultad o a un departamento",
                 id="sin-facultad-ni-departamento"),
])
def test_programa_invalido(datos, mensaje):
    """REQ-3: el programa debe ir asociado a una facultad o a un departamento."""
    with pytest.raises(DatoInvalidoError, match=mensaje):
        validar_datos_programa(datos)


@pytest.mark.parametrize("datos", [
    pytest.param(PROGRAMA, id="con-facultad"),
    pytest.param({**sin(PROGRAMA, "facultad_id"), "departamento_id": 1}, id="con-departamento"),
    pytest.param({**PROGRAMA, "departamento_id": 1}, id="con-los-dos"),
])
def test_programa_valido(datos):
    """Basta con una de las dos asociaciones."""
    validar_datos_programa(datos)


def test_limpiar_texto_y_dominio_valido():
    """Funciones auxiliares de normalización."""
    assert limpiar_texto("  Facultad   de  Artes ") == "Facultad de Artes"
    assert dominio_valido("itm.edu.co")
    assert not dominio_valido("sinpunto")
    assert not dominio_valido("con espacio.co")
