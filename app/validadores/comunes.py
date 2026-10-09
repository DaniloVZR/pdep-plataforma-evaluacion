"""Comprobaciones de tipo que comparten los validadores."""


def es_entero_positivo(valor: object) -> bool:
    """``True`` solo para enteros mayores que cero.

    ``bool`` se excluye a propósito: ``True`` es un ``int`` en Python y, sin
    esta condición, ``{"programa_id": true}`` pasaría como el id 1.
    """
    return isinstance(valor, int) and not isinstance(valor, bool) and valor > 0


def es_texto_no_vacio(valor: object) -> bool:
    """``True`` para cadenas con al menos un carácter distinto de espacio."""
    return isinstance(valor, str) and valor.strip() != ""


def es_lista_de_ids(valor: object) -> bool:
    """``True`` si es una lista cuyos elementos son enteros positivos."""
    return isinstance(valor, list) and all(es_entero_positivo(item) for item in valor)
