"""Entidades del dominio que usan HU-003, HU-005 y HU-007.

Son ``dataclasses`` inmutables: no conocen la base de datos ni Flask, por lo
que su lógica se prueba con objetos creados en memoria.
"""

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from enum import Enum
import math

from app.dominio.errores import NotaFueraDeRangoError, TipoNotaInvalidoError

# Margen aceptado al sumar los pesos: 0.1 + 0.2 + 0.7 da 0.9999999999999999 en
# punto flotante y debe considerarse igual a 1.
TOLERANCIA_PESOS = 1e-6


class Rol(str, Enum):
    """Roles que se pueden registrar en HU-003."""

    ESTUDIANTE = "ESTUDIANTE"
    DOCENTE = "DOCENTE"


class Modalidad(str, Enum):
    """Modalidad del proyecto (RN009)."""

    PA = "PA"     # Proyecto de Aula: una asignatura
    PIA = "PIA"   # Proyecto Integrador: dos o más asignaturas


class EstadoEvaluacion(str, Enum):
    """Ciclo de vida de una evaluación."""

    PENDIENTE = "PENDIENTE"     # creada al asignar el evaluador (HU-006)
    BORRADOR = "BORRADOR"       # tiene notas, pero el evaluador no la confirmó
    CONFIRMADA = "CONFIRMADA"   # cerrada: el puntaje es visible (RN007)


@dataclass(frozen=True)
class Usuario:
    """Estudiante o docente registrado por el administrador."""

    id: int | None
    nombres: str
    correo: str
    rol: Rol
    programa_id: int
    asignatura_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class Feria:
    """Feria de proyectos con su plazo de inscripción."""

    id: int
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    asignatura_ids: frozenset[int] = frozenset()

    def acepta_asignaturas(self, asignatura_ids: frozenset[int]) -> bool:
        """Indica si todas las asignaturas participan en la feria."""
        return asignatura_ids <= self.asignatura_ids


@dataclass(frozen=True)
class Proyecto:
    """Proyecto inscrito por un equipo en una feria."""

    id: int | None
    equipo_id: int
    feria_id: int
    nombre: str
    descripcion: str
    modalidad: Modalidad
    asignatura_ids: tuple[int, ...]
    fecha_inscripcion: date


@dataclass(frozen=True)
class Criterio:
    """Criterio de la rúbrica con su peso (fracción entre 0 y 1)."""

    id: int
    nombre: str
    peso: float


@dataclass(frozen=True)
class Rubrica:
    """Rúbrica de una feria: criterios con peso y escala de notas."""

    id: int
    feria_id: int
    nota_minima: float
    nota_maxima: float
    criterios: tuple[Criterio, ...] = ()

    def ids_criterios(self) -> frozenset[int]:
        """Identificadores de los criterios de la rúbrica."""
        return frozenset(criterio.id for criterio in self.criterios)

    def pesos_validos(self) -> bool:
        """Todos los pesos son positivos y su suma es 1 dentro de la tolerancia."""
        if any(criterio.peso <= 0 for criterio in self.criterios):
            return False
        suma = sum(criterio.peso for criterio in self.criterios)
        return abs(suma - 1.0) <= TOLERANCIA_PESOS

    def validar_nota(self, nota: object) -> float:
        """Devuelve la nota como ``float`` o lanza el error que corresponda.

        ``bool`` se rechaza aunque en Python sea subclase de ``int``, y NaN o
        infinito se rechazan porque cualquier comparación con NaN da ``False``
        y la nota pasaría el control de rango.
        """
        es_numero = isinstance(nota, (int, float)) and not isinstance(nota, bool)
        if not es_numero or not math.isfinite(nota):
            raise TipoNotaInvalidoError(f"La nota {nota!r} no es un número válido.")
        if nota < self.nota_minima or nota > self.nota_maxima:
            raise NotaFueraDeRangoError(
                f"La nota {nota} está fuera de la escala "
                f"{self.nota_minima}–{self.nota_maxima}."
            )
        return float(nota)

    def calcular_puntaje(self, notas: dict[int, object]) -> float:
        """Recorre los criterios y acumula nota × peso (RN006)."""
        puntaje = 0.0
        for criterio in self.criterios:
            nota = self.validar_nota(notas[criterio.id])
            puntaje += nota * criterio.peso
        return round(puntaje, 2)


@dataclass(frozen=True)
class Evaluacion:
    """Evaluación de un proyecto por un evaluador asignado."""

    id: int
    proyecto_id: int
    evaluador_id: int
    feria_id: int
    estado: EstadoEvaluacion
    puntaje_final: float | None = None
    fecha_confirmacion: datetime | None = None
    notas: dict[int, float] = field(default_factory=dict)

    @property
    def puntaje_visible(self) -> float | None:
        """El puntaje solo se publica cuando la evaluación está confirmada (RN007)."""
        if self.estado is EstadoEvaluacion.CONFIRMADA:
            return self.puntaje_final
        return None

    def con_calificacion(self, notas: dict[int, float], puntaje: float,
                         confirmada: bool, momento: datetime) -> "Evaluacion":
        """Devuelve una copia con las notas, el puntaje y el nuevo estado."""
        if confirmada:
            return replace(self, notas=notas, puntaje_final=puntaje,
                           estado=EstadoEvaluacion.CONFIRMADA,
                           fecha_confirmacion=momento)
        return replace(self, notas=notas, puntaje_final=puntaje,
                       estado=EstadoEvaluacion.BORRADOR, fecha_confirmacion=None)
