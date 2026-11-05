"""Entidades del dominio que usan HU-001 a HU-007, HU-009 y HU-010.

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

# Escala de notas de las rúbricas que se crean con una feria (HU-004); es la misma que usa
# HU-007 con los datos de demostración.
NOTA_MINIMA = 1.0
NOTA_MAXIMA = 5.0


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
class Institucion:
    """Institución educativa (HU-001, REQ-1). ``dominio`` es el del correo institucional (RN001)."""

    id: int | None
    nombre: str
    nit: str
    correo_contacto: str = ""
    telefono: str = ""
    dominio: str = ""


@dataclass(frozen=True)
class Facultad:
    """Facultad de una institución (HU-001, REQ-2)."""

    id: int | None
    institucion_id: int
    nombre: str


@dataclass(frozen=True)
class Departamento:
    """Departamento de una institución (HU-001, REQ-2)."""

    id: int | None
    institucion_id: int
    nombre: str


@dataclass(frozen=True)
class Programa:
    """Programa académico asociado a una facultad o a un departamento (HU-001, REQ-3)."""

    id: int | None
    institucion_id: int
    codigo: str
    nombre: str
    facultad_id: int | None = None
    departamento_id: int | None = None


@dataclass(frozen=True)
class Asignatura:
    """Asignatura asociada a un programa académico (HU-002, REQ-4)."""

    id: int | None
    programa_id: int
    codigo: str
    nombre: str
    semestre: int


@dataclass(frozen=True)
class Usuario:
    """Estudiante o docente registrado por el administrador."""

    id: int | None
    nombres: str
    correo: str
    rol: Rol
    programa_id: int
    asignatura_ids: tuple[int, ...] = ()


class RolCuenta(str, Enum):
    """Rol con el que se entra a la plataforma (RNF-03). Son los actores del RTF1."""

    ADMINISTRADOR = "ADMINISTRADOR"
    EVALUADOR = "EVALUADOR"
    ESTUDIANTE = "ESTUDIANTE"


@dataclass(frozen=True)
class Cuenta:
    """Cuenta de acceso (RNF-03).

    Está separada de ``Usuario`` para no cambiar el registro de HU-003. El
    administrador no es un usuario académico, así que su ``usuario_id`` es ``None``.
    """

    correo: str
    clave: str
    rol: RolCuenta
    usuario_id: int | None
    nombre: str


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
class Asignacion:
    """Evaluador asignado a un proyecto (HU-006). Crea la evaluación en estado PENDIENTE."""

    evaluacion_id: int
    proyecto_id: int
    evaluador_id: int


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
    retroalimentacion: str = ""

    @property
    def puntaje_visible(self) -> float | None:
        """El puntaje solo se publica cuando la evaluación está confirmada (RN007)."""
        if self.estado is EstadoEvaluacion.CONFIRMADA:
            return self.puntaje_final
        return None

    def con_calificacion(self, notas: dict[int, float], puntaje: float,
                         confirmada: bool, momento: datetime,
                         retroalimentacion: str = "") -> "Evaluacion":
        """Devuelve una copia con las notas, el puntaje, la retroalimentación y el nuevo
        estado."""
        if confirmada:
            return replace(self, notas=notas, puntaje_final=puntaje,
                           estado=EstadoEvaluacion.CONFIRMADA,
                           fecha_confirmacion=momento, retroalimentacion=retroalimentacion)
        return replace(self, notas=notas, puntaje_final=puntaje,
                       estado=EstadoEvaluacion.BORRADOR, fecha_confirmacion=None,
                       retroalimentacion=retroalimentacion)


@dataclass(frozen=True)
class ResultadoEvaluacion:
    """Lo que un evaluador dejó sobre un proyecto, tal como lo consulta el estudiante (HU-009).

    ``puntaje_final`` y ``retroalimentacion`` valen ``None`` cuando están ocultos.
    """

    evaluacion_id: int
    evaluador: str
    estado: EstadoEvaluacion
    puntaje_final: float | None
    retroalimentacion: str | None
    fecha_confirmacion: datetime | None

    def publicada(self) -> "ResultadoEvaluacion":
        """RN007: mientras no esté confirmada se ocultan el puntaje y la retroalimentación."""
        if self.estado is EstadoEvaluacion.CONFIRMADA:
            return self
        return replace(self, puntaje_final=None, retroalimentacion=None)


@dataclass(frozen=True)
class ResultadoProyecto:
    """Proyecto del estudiante con las evaluaciones de sus evaluadores (HU-009)."""

    proyecto_id: int
    proyecto: str
    feria: str
    equipo: str
    evaluaciones: tuple[ResultadoEvaluacion, ...] = ()


class Agrupacion(str, Enum):
    """Cómo se agrupa el reporte de resultados (HU-010, REQ-19)."""

    FERIA = "feria"
    ASIGNATURA = "asignatura"
    PROGRAMA = "programa"


@dataclass(frozen=True)
class FiltrosReporte:
    """Filtros del reporte (HU-010). Un id en ``None`` significa "sin filtrar por eso"."""

    agrupar_por: Agrupacion = Agrupacion.FERIA
    feria_id: int | None = None
    asignatura_id: int | None = None
    programa_id: int | None = None


@dataclass(frozen=True)
class AsignaturaReporte:
    """Asignatura de un proyecto con el programa al que pertenece (HU-010)."""

    id: int
    nombre: str
    programa_id: int
    programa: str


@dataclass(frozen=True)
class ProyectoReporte:
    """Proyecto con el estado y el puntaje de cada una de sus evaluaciones (HU-010).

    ``evaluaciones`` son pares ``(estado, puntaje_final)``.
    """

    proyecto_id: int
    proyecto: str
    equipo: str
    modalidad: Modalidad
    feria_id: int
    feria: str
    asignaturas: tuple[AsignaturaReporte, ...] = ()
    evaluaciones: tuple[tuple[EstadoEvaluacion, float | None], ...] = ()

    def puntaje_consolidado(self) -> float | None:
        """REQ-18: promedio de los puntajes cuando TODAS sus evaluaciones están confirmadas.

        Devuelve ``None`` si el proyecto no tiene evaluadores o si alguna evaluación sigue
        pendiente o en borrador: ese proyecto no entra al reporte (criterio de aceptación 1).
        """
        if not self.evaluaciones:
            return None
        if any(estado is not EstadoEvaluacion.CONFIRMADA for estado, _ in self.evaluaciones):
            return None
        puntajes = [puntaje for _, puntaje in self.evaluaciones]
        return round(sum(puntajes) / len(puntajes), 2)


@dataclass(frozen=True)
class ProyectoConsolidado:
    """Fila del reporte: un proyecto con su puntaje consolidado (HU-010)."""

    proyecto_id: int
    proyecto: str
    equipo: str
    modalidad: Modalidad
    feria: str
    puntaje: float
    evaluaciones: int


@dataclass(frozen=True)
class GrupoReporte:
    """Una feria, asignatura o programa del reporte con sus proyectos, de mayor a menor."""

    id: int
    nombre: str
    proyectos: tuple[ProyectoConsolidado, ...]

    @property
    def promedio(self) -> float:
        """Promedio de los puntajes del grupo. Un grupo siempre tiene al menos un proyecto."""
        return round(sum(p.puntaje for p in self.proyectos) / len(self.proyectos), 2)

    @property
    def maximo(self) -> float:
        """Puntaje más alto del grupo."""
        return max(p.puntaje for p in self.proyectos)

    @property
    def minimo(self) -> float:
        """Puntaje más bajo del grupo."""
        return min(p.puntaje for p in self.proyectos)


@dataclass(frozen=True)
class Reporte:
    """Reporte consolidado de resultados (HU-010, REQ-18 y REQ-19).

    ``pendientes`` cuenta los proyectos que cumplen los filtros pero no entran al reporte
    porque les falta alguna evaluación confirmada.
    """

    filtros: FiltrosReporte
    grupos: tuple[GrupoReporte, ...]
    consolidados: int
    pendientes: int
    promedio_general: float | None
