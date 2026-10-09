"""HU-003 · Condiciones internas de ``validar_datos_registro`` y del dominio del correo."""

import pytest

from app.dominio.errores import DatoInvalidoError
from app.validadores.usuario_validador import (
    dominio_es_institucional,
    extraer_dominio,
    normalizar_correo,
    validar_datos_registro,
)

VALIDO = {"nombres": "Ana", "correo": "ana@pascualbravo.edu.co", "rol": "DOCENTE",
          "programa_id": 1, "asignatura_ids": [1]}
DOMINIOS = frozenset({"pascualbravo.edu.co"})


def con(**cambios):
    """Copia de la solicitud válida con algunos campos cambiados."""
    return {**VALIDO, **cambios}


def sin(campo):
    """Copia de la solicitud válida sin un campo."""
    return {clave: valor for clave, valor in VALIDO.items() if clave != campo}


@pytest.mark.parametrize("datos", [
    pytest.param(None, id="cuerpo-nulo"),
    pytest.param(["ana"], id="cuerpo-lista"),
    pytest.param(sin("nombres"), id="nombres-ausente"),
    pytest.param(con(nombres=None), id="nombres-nulo"),
    pytest.param(con(nombres=""), id="nombres-vacio"),
    pytest.param(con(nombres="   "), id="nombres-solo-espacios"),
    pytest.param(con(nombres=123), id="nombres-numero"),
    pytest.param(con(correo=None), id="correo-nulo"),
    pytest.param(con(rol="ADMIN"), id="rol-no-permitido"),
    pytest.param(sin("programa_id"), id="programa-ausente"),
    pytest.param(con(programa_id=0), id="programa-cero"),
    pytest.param(con(programa_id=-1), id="programa-negativo"),
    pytest.param(con(programa_id="1"), id="programa-texto"),
    pytest.param(con(programa_id=True), id="programa-booleano"),
    pytest.param(con(programa_id=1.5), id="programa-decimal"),
    pytest.param(con(asignatura_ids="1"), id="asignaturas-texto"),
    pytest.param(con(asignatura_ids=[0]), id="asignatura-cero"),
    pytest.param(con(asignatura_ids=[1, None]), id="asignatura-nula"),
])
def test_datos_invalidos_lanzan_dato_invalido(datos):
    """Cada condición falsa de D1 termina en ``DatoInvalidoError``."""
    with pytest.raises(DatoInvalidoError):
        validar_datos_registro(datos)


@pytest.mark.parametrize("datos", [
    pytest.param(VALIDO, id="completo"),
    pytest.param(sin("asignatura_ids"), id="sin-asignaturas"),
    pytest.param(con(rol=" docente "), id="rol-minusculas-con-espacios"),
])
def test_datos_validos_no_lanzan(datos):
    """Las variantes aceptadas pasan sin excepción."""
    validar_datos_registro(datos)


@pytest.mark.parametrize(("correo", "esperado"), [
    pytest.param("ana@pascualbravo.edu.co", True, id="dominio-exacto"),
    pytest.param("ana@gmail.com", False, id="proveedor-personal"),
    pytest.param("ana@pascualbravo.edu.co.falso.com", False, id="contiene-dominio"),
    pytest.param("ana@mail.pascualbravo.edu.co", False, id="subdominio"),
    pytest.param("ana@b@pascualbravo.edu.co", False, id="dos-arrobas"),
    pytest.param("@pascualbravo.edu.co", False, id="sin-usuario"),
    pytest.param("ana.pascualbravo.edu.co", False, id="sin-arroba"),
])
def test_dominio_es_institucional(correo, esperado):
    """La comparación del dominio es exacta (RN001, RNF-03)."""
    assert dominio_es_institucional(correo, DOMINIOS) is esperado


def test_normalizar_correo_quita_espacios_y_mayusculas():
    """El mismo correo escrito distinto produce el mismo valor."""
    assert normalizar_correo("  ANA@PascualBravo.edu.co ") == "ana@pascualbravo.edu.co"


def test_extraer_dominio_de_correo_mal_formado_es_vacio():
    """Sin exactamente una arroba no hay dominio."""
    assert extraer_dominio("ana") == ""
