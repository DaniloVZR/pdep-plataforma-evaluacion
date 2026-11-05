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


# Escala de 1 a 5 de las rúbricas (HU-004): 3.0 aprueba, como en la institución.
NOTA_APROBATORIA = 3.0


class NivelDesempeno(str, Enum):
    """Nivel del puntaje consolidado de un proyecto (HU-010)."""

    EXCELENTE = "EXCELENTE"         # 4.5 a 5.0
    BUENO = "BUENO"                 # 4.0 a 4.49
    ACEPTABLE = "ACEPTABLE"         # 3.0 a 3.99
    INSUFICIENTE = "INSUFICIENTE"   # menos de 3.0: reprobado

    @classmethod
    def de(cls, puntaje: float) -> "NivelDesempeno":
        """Nivel que corresponde al puntaje."""
        if puntaje >= 4.5:
            return cls.EXCELENTE
        if puntaje >= 4.0:
            return cls.BUENO
        if puntaje >= NOTA_APROBATORIA:
            return cls.ACEPTABLE
        return cls.INSUFICIENTE


@dataclass(frozen=True)
class Distribucion:
    """Cuántos proyectos quedaron en cada nivel de desempeño (HU-010)."""

    excelente: int = 0
    bueno: int = 0
    aceptable: int = 0
    insuficiente: int = 0

    @classmethod
    def de_puntajes(cls, puntajes: list[float]) -> "Distribucion":
        """Cuenta los puntajes por nivel."""
        niveles = [NivelDesempeno.de(p) for p in puntajes]
        return cls(*(niveles.count(nivel) for nivel in NivelDesempeno))

    @property
    def aprobados(self) -> int:
        """Proyectos con puntaje de 3.0 o más."""
        return self.excelente + self.bueno + self.aceptable

    @property
    def reprobados(self) -> int:
        """Proyectos con puntaje menor que 3.0."""
        return self.insuficiente


@dataclass(frozen=True)
class AsignaturaReporte:
    """Asignatura de un proyecto con el programa al que pertenece (HU-010)."""

    id: int
    nombre: str
    programa_id: int
    programa: str


@dataclass(frozen=True)
class NotaCriterio:
    """Nota de un criterio de la rúbrica, o el promedio de varias (HU-010)."""

    criterio: str
    peso: float
    nota: float


def promediar_criterios(notas: list[NotaCriterio]) -> tuple[NotaCriterio, ...]:
    """Promedio por criterio, en el orden en que aparece cada uno.

    Se agrupa por nombre porque, al agrupar por asignatura o programa, un grupo puede
    reunir proyectos de ferias con rúbricas distintas.
    """
    por_criterio: dict[str, list[NotaCriterio]] = {}
    for nota in notas:
        por_criterio.setdefault(nota.criterio, []).append(nota)
    return tuple(
        NotaCriterio(nombre, lista[0].peso, round(sum(n.nota for n in lista) / len(lista), 2))
        for nombre, lista in por_criterio.items())


@dataclass(frozen=True)
class EvaluacionReporte:
    """Una evaluación tal como la usa el reporte: estado, puntaje, notas y comentario."""

    evaluador: str
    estado: EstadoEvaluacion
    puntaje_final: float | None = None
    fecha_confirmacion: datetime | None = None
    retroalimentacion: str = ""
    notas: tuple[NotaCriterio, ...] = ()


@dataclass(frozen=True)
class ProyectoReporte:
    """Proyecto con sus integrantes, asignaturas y todas sus evaluaciones (HU-010)."""

    proyecto_id: int
    proyecto: str
    equipo: str
    modalidad: Modalidad
    feria_id: int
    feria: str
    integrantes: tuple[str, ...] = ()
    asignaturas: tuple[AsignaturaReporte, ...] = ()
    evaluaciones: tuple[EvaluacionReporte, ...] = ()

    def evaluacion_completa(self) -> bool:
        """Criterio de aceptación 1: tiene evaluadores y TODAS sus evaluaciones están
        confirmadas."""
        return bool(self.evaluaciones) and all(
            e.estado is EstadoEvaluacion.CONFIRMADA for e in self.evaluaciones)

    def puntaje_consolidado(self) -> float | None:
        """REQ-18: promedio de los puntajes de sus evaluadores; ``None`` si la evaluación
        no está completa (ese proyecto no entra al reporte)."""
        if not self.evaluacion_completa():
            return None
        puntajes = [e.puntaje_final for e in self.evaluaciones]
        return round(sum(puntajes) / len(puntajes), 2)

    def criterios(self) -> tuple[NotaCriterio, ...]:
        """Promedio de cada criterio entre sus evaluadores."""
        return promediar_criterios([n for e in self.evaluaciones for n in e.notas])


@dataclass(frozen=True)
class ProyectoConsolidado:
    """Fila del reporte: un proyecto con su puntaje consolidado y su detalle (HU-010)."""

    proyecto_id: int
    proyecto: str
    equipo: str
    modalidad: Modalidad
    feria: str
    puntaje: float
    integrantes: tuple[str, ...] = ()
    asignaturas: tuple[str, ...] = ()
    criterios: tuple[NotaCriterio, ...] = ()
    evaluaciones: tuple[EvaluacionReporte, ...] = ()

    @property
    def nivel(self) -> NivelDesempeno:
        """Nivel de desempeño del puntaje."""
        return NivelDesempeno.de(self.puntaje)


@dataclass(frozen=True)
class GrupoReporte:
    """Una feria, asignatura o programa del reporte con sus proyectos, de mayor a menor."""

    id: int
    nombre: str
    proyectos: tuple[ProyectoConsolidado, ...]

    def _puntajes(self) -> list[float]:
        return [p.puntaje for p in self.proyectos]

    @property
    def promedio(self) -> float:
        """Promedio de los puntajes del grupo. Un grupo siempre tiene al menos un proyecto."""
        return round(sum(self._puntajes()) / len(self.proyectos), 2)

    @property
    def maximo(self) -> float:
        """Puntaje más alto del grupo."""
        return max(self._puntajes())

    @property
    def minimo(self) -> float:
        """Puntaje más bajo del grupo."""
        return min(self._puntajes())

    @property
    def distribucion(self) -> Distribucion:
        """Proyectos del grupo por nivel de desempeño."""
        return Distribucion.de_puntajes(self._puntajes())

    @property
    def criterios(self) -> tuple[NotaCriterio, ...]:
        """Promedio de cada criterio en el grupo: fortalezas y debilidades."""
        return promediar_criterios([c for p in self.proyectos for c in p.criterios])


@dataclass(frozen=True)
class ProyectoPendiente:
    """Proyecto que no entra al reporte y las evaluaciones que le faltan (HU-010).

    ``faltantes`` vacío significa que no tiene evaluadores asignados.
    """

    proyecto_id: int
    proyecto: str
    equipo: str
    feria: str
    confirmadas: int
    total: int
    faltantes: tuple[EvaluacionReporte, ...] = ()


@dataclass(frozen=True)
class AvanceEvaluacion:
    """Avance de las evaluaciones de los proyectos que cumplen los filtros (HU-010)."""

    total: int = 0
    confirmadas: int = 0
    borradores: int = 0
    sin_empezar: int = 0
    proyectos_sin_evaluador: int = 0

    @property
    def porcentaje(self) -> float:
        """Porcentaje de evaluaciones confirmadas; 0 si no hay evaluaciones."""
        return round(self.confirmadas * 100 / self.total, 1) if self.total else 0.0


@dataclass(frozen=True)
class Reporte:
    """Reporte consolidado de resultados (HU-010, REQ-18 y REQ-19).

    ``filtros_aplicados`` son pares ``(filtro, nombre)``, por ejemplo
    ``("Feria", "Feria de Proyectos 2026-2")``; ``generado`` deja constancia de cuándo se
    generó (RNF-06).
    """

    filtros: FiltrosReporte
    filtros_aplicados: tuple[tuple[str, str], ...]
    generado: datetime
    grupos: tuple[GrupoReporte, ...]
    consolidados: int
    promedio_general: float | None
    distribucion: Distribucion
    avance: AvanceEvaluacion
    pendientes: tuple[ProyectoPendiente, ...]
