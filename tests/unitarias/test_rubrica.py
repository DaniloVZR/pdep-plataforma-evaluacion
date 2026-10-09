"""HU-007 · Condiciones internas de la rúbrica: pesos, tipo y rango de cada nota."""

import time

import pytest

from app.dominio.errores import (
    DatoInvalidoError,
    NotaFueraDeRangoError,
    NotasIncompletasError,
    TipoNotaInvalidoError,
)
from app.dominio.modelos import Criterio, Rubrica
from app.validadores.calificacion_validador import (
    validar_notas_completas,
    validar_solicitud_calificacion,
)


def rubrica_con_pesos(*pesos):
    """Rúbrica de escala 1.0–5.0 con un criterio por cada peso."""
    criterios = tuple(Criterio(i, f"C{i}", peso) for i, peso in enumerate(pesos, start=1))
    return Rubrica(id=1, feria_id=1, nota_minima=1.0, nota_maxima=5.0, criterios=criterios)


RUBRICA = rubrica_con_pesos(0.5, 0.3, 0.2)


@pytest.mark.parametrize(("pesos", "esperado"), [
    pytest.param((0.5, 0.3, 0.2), True, id="suma-exacta"),
    pytest.param((0.1, 0.2, 0.7), True, id="suma-0.9999999999999999-dentro-de-tolerancia"),
    pytest.param((1.0,), True, id="un-criterio"),
    pytest.param((0.5, 0.3), False, id="suma-0.8"),
    pytest.param((0.6, 0.6), False, id="suma-1.2"),
    pytest.param((0.5, 0.5, 0.0), False, id="peso-cero"),
    pytest.param((1.2, -0.2), False, id="peso-negativo-que-compensa"),
    pytest.param((0.5, 0.49999), False, id="diferencia-1e-5-fuera-de-tolerancia"),
])
def test_pesos_validos(pesos, esperado):
    """Pesos positivos y suma 1 con tolerancia de 1e-6."""
    assert rubrica_con_pesos(*pesos).pesos_validos() is esperado


@pytest.mark.parametrize("nota", [
    pytest.param(1.0, id="minimo"),
    pytest.param(5.0, id="maximo"),
    pytest.param(3, id="entero"),
])
def test_notas_aceptadas(nota):
    """Los extremos de la escala son válidos."""
    assert RUBRICA.validar_nota(nota) == float(nota)


@pytest.mark.parametrize("nota", [
    pytest.param(0.99, id="bajo-el-minimo"),
    pytest.param(5.01, id="sobre-el-maximo"),
    pytest.param(-1, id="negativa"),
])
def test_notas_fuera_de_rango(nota):
    """Un centésimo fuera de la escala ya se rechaza."""
    with pytest.raises(NotaFueraDeRangoError):
        RUBRICA.validar_nota(nota)


@pytest.mark.parametrize("nota", [
    pytest.param("4.5", id="texto"),
    pytest.param(None, id="nulo"),
    pytest.param(True, id="booleano"),
    pytest.param(float("nan"), id="NaN"),
    pytest.param(float("inf"), id="infinito"),
    pytest.param([4.5], id="lista"),
])
def test_notas_de_tipo_invalido(nota):
    """NaN pasaría la comparación de rango (toda comparación con NaN es False)."""
    with pytest.raises(TipoNotaInvalidoError):
        RUBRICA.validar_nota(nota)


def test_calcular_puntaje_redondea_a_dos_decimales():
    """3.3×0.5 + 4.1×0.3 + 2.7×0.2 = 3.42."""
    assert RUBRICA.calcular_puntaje({1: 3.3, 2: 4.1, 3: 2.7}) == 3.42


@pytest.mark.parametrize("notas", [
    pytest.param({1: 4.0, 2: 3.0}, id="falta-un-criterio"),
    pytest.param({1: 4.0, 2: 3.0, 3: 5.0, 4: 1.0}, id="criterio-que-no-existe"),
])
def test_notas_incompletas(notas):
    """Debe llegar exactamente una nota por criterio."""
    with pytest.raises(NotasIncompletasError):
        validar_notas_completas(RUBRICA, notas)


@pytest.mark.parametrize("datos", [
    pytest.param(None, id="cuerpo-nulo"),
    pytest.param({"evaluador_id": "2", "notas": {"1": 4}}, id="evaluador-texto"),
    pytest.param({"evaluador_id": 2, "notas": {}}, id="notas-vacias"),
    pytest.param({"evaluador_id": 2, "notas": [4, 3]}, id="notas-lista"),
    pytest.param({"evaluador_id": 2, "notas": {"1": 4}, "confirmar": 1}, id="confirmar-entero"),
    pytest.param({"evaluador_id": 2, "notas": {"abc": 4}}, id="clave-no-numerica"),
])
def test_solicitudes_mal_formadas(datos):
    """Cada condición falsa de D1 lanza ``DatoInvalidoError``."""
    with pytest.raises(DatoInvalidoError):
        validar_solicitud_calificacion(datos)


def test_solicitud_valida_convierte_claves_y_confirmar_por_defecto():
    """``{"7": 4.5}`` se convierte en ``{7: 4.5}`` y ``confirmar`` vale False si no llega."""
    assert validar_solicitud_calificacion({"evaluador_id": 2, "notas": {"7": 4.5}}) == \
        (2, {7: 4.5}, False)


def test_rnf01_calculo_de_500_proyectos_en_menos_de_5_segundos():
    """RNF-01: 500 proyectos con 5 criterios cada uno."""
    rubrica = rubrica_con_pesos(0.2, 0.2, 0.2, 0.2, 0.2)
    notas = {1: 4.0, 2: 3.5, 3: 5.0, 4: 2.0, 5: 4.5}
    inicio = time.perf_counter()
    for _ in range(500):
        rubrica.calcular_puntaje(notas)
    assert time.perf_counter() - inicio < 5.0
