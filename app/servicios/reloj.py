"""Fuente de la fecha y la hora actuales.

Los servicios no llaman a ``date.today()`` directamente: reciben un reloj. En
las pruebas se inyecta un reloj con una fecha fija para recorrer los límites
del plazo (un día antes del inicio, el día de inicio, el día de fin y un día
después) sin depender del día en que se ejecutan.
"""

from datetime import date, datetime
from typing import Protocol
from zoneinfo import ZoneInfo

ZONA_HORARIA = ZoneInfo("America/Bogota")


class Reloj(Protocol):
    """Contrato del reloj que usan los servicios."""

    def hoy(self) -> date:
        """Fecha actual, sin hora."""

    def ahora(self) -> datetime:
        """Fecha y hora actuales con zona horaria."""


class RelojSistema:
    """Reloj real, en la zona horaria de Colombia."""

    def hoy(self) -> date:
        """Fecha actual en Bogotá."""
        return self.ahora().date()

    def ahora(self) -> datetime:
        """Fecha y hora actuales en Bogotá."""
        return datetime.now(ZONA_HORARIA)
