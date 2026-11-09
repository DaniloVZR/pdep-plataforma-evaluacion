"""HU-008 · REQ-16 · RN006: el puntaje final se calcula solo y no se escribe a mano."""

import pytest

from app.dominio.errores import DatoInvalidoError, PuntajeNoEditableError
from app.dominio.modelos import Criterio, Rubrica
from app.validadores.calificacion_validador import rechazar_puntaje_manual


RUBRICA = Rubrica(id=1, feria_id=1, nota_minima=1.0, nota_maxima=5.0, criterios=(
    Criterio(1, "Funcionalidad", 0.5),
    Criterio(2, "Presentación", 0.3),
    Criterio(3, "Documentación", 0.2),
))


@pytest.mark.parametrize("campo", ["puntaje_final", "puntaje"])
@pytest.mark.parametrize("valor", [5.0, None, "5"])
def test_rechaza_cualquier_puntaje_enviado(campo, valor):
    """Basta con que el campo exista, tenga el valor que tenga."""
    with pytest.raises(PuntajeNoEditableError) as error:
        rechazar_puntaje_manual({"evaluador_id": 1, "notas": {"1": 4}, campo: valor})
    assert error.value.codigo == "puntaje_no_editable"
    assert error.value.estado_http == 400


def test_el_rechazo_es_un_dato_invalido():
    """Hereda de DatoInvalidoError, así que el manejador global responde 400."""
    assert issubclass(PuntajeNoEditableError, DatoInvalidoError)


def test_solicitud_sin_puntaje_pasa():
    """La solicitud normal de HU-007 (notas, confirmar y retroalimentación) no se toca."""
    rechazar_puntaje_manual({"evaluador_id": 1, "notas": {"1": 4}, "confirmar": True,
                             "retroalimentacion": "Buen trabajo"})


@pytest.mark.parametrize("notas, esperado", [
    ({1: 5.0, 2: 5.0, 3: 5.0}, 5.0),     # notas en el máximo
    ({1: 1.0, 2: 1.0, 3: 1.0}, 1.0),     # notas en el mínimo
    ({1: 4.0, 2: 3.0, 3: 5.0}, 3.9),     # 2.0 + 0.9 + 1.0
    ({1: 3.3, 2: 4.7, 3: 2.1}, 3.48),    # 1.65 + 1.41 + 0.42
])
def test_puntaje_es_la_suma_de_nota_por_peso(notas, esperado):
    """Criterio 1 de HU-008: Puntaje = Σ (nota × peso), redondeado a dos decimales."""
    assert RUBRICA.calcular_puntaje(notas) == esperado


def test_mismo_puntaje_con_las_notas_en_otro_orden():
    """El resultado depende de las notas y los pesos, no del orden en que llegan."""
    assert RUBRICA.calcular_puntaje({3: 5.0, 1: 4.0, 2: 3.0}) == \
        RUBRICA.calcular_puntaje({1: 4.0, 2: 3.0, 3: 5.0})
