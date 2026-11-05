"""Validación de los filtros del reporte de resultados (HU-010)."""

from collections.abc import Mapping

from app.dominio.errores import DatoInvalidoError
from app.dominio.modelos import Agrupacion, FiltrosReporte

FILTROS_ID = ("feria_id", "asignatura_id", "programa_id")


def _leer_id(parametros: Mapping[str, str], nombre: str) -> int | None:
    """``None`` si el parámetro no viene o viene vacío; un entero mayor que 0 si es válido.

    Los parámetros de la URL llegan como texto. ``isdecimal()`` rechaza "-1", "1.5" y "abc";
    también se rechazan "0" y los números de más de 18 cifras, que no caben en un entero de
    SQLite. Así un filtro mal escrito responde 400 en lugar de ignorarse en silencio.
    """
    valor = parametros.get(nombre, "").strip()
    if valor == "":
        return None
    if not valor.isdecimal() or len(valor) > 18 or int(valor) == 0:
        raise DatoInvalidoError(f"El parámetro '{nombre}' debe ser un entero mayor que 0.")
    return int(valor)


def leer_filtros(parametros: Mapping[str, str]) -> FiltrosReporte:
    """REQ-19: ``agrupar_por`` es feria (por defecto), asignatura o programa; los tres ids
    son opcionales y se pueden combinar."""
    agrupar_por = parametros.get("agrupar_por", "").strip().lower() or Agrupacion.FERIA.value
    if agrupar_por not in {agrupacion.value for agrupacion in Agrupacion}:
        raise DatoInvalidoError(
            "El parámetro 'agrupar_por' debe ser feria, asignatura o programa.")
    ids = {nombre: _leer_id(parametros, nombre) for nombre in FILTROS_ID}
    return FiltrosReporte(agrupar_por=Agrupacion(agrupar_por), **ids)
