"""Caso de uso HU-010: consolidar y generar reportes de resultados (REQ-18, REQ-19)."""

from collections.abc import Mapping

from app.dominio.errores import (
    AsignaturaNoEncontradaError,
    FeriaNoEncontradaError,
    ProgramaNoEncontradoError,
)
from app.dominio.modelos import (
    Agrupacion,
    AvanceEvaluacion,
    Distribucion,
    EstadoEvaluacion,
    FiltrosReporte,
    GrupoReporte,
    ProyectoConsolidado,
    ProyectoPendiente,
    ProyectoReporte,
    Reporte,
)
from app.repositorios.contratos import ReporteRepositorio
from app.servicios.reloj import Reloj
from app.validadores.reporte_validador import leer_filtros


def _claves_de_grupo(proyecto: ProyectoReporte,
                     agrupar_por: Agrupacion) -> list[tuple[int, str]]:
    """Grupos a los que pertenece el proyecto, como pares ``(id, nombre)``.

    Un Proyecto Integrador (PIA) tiene varias asignaturas, así que aparece en el grupo de
    cada una. Si sus asignaturas son del mismo programa, aparece una sola vez en ese
    programa.
    """
    if agrupar_por is Agrupacion.FERIA:                                     # G1
        return [(proyecto.feria_id, proyecto.feria)]
    if agrupar_por is Agrupacion.ASIGNATURA:                                # G2
        return [(a.id, a.nombre) for a in proyecto.asignaturas]
    return list(dict.fromkeys((a.programa_id, a.programa) for a in proyecto.asignaturas))


def consolidar(proyecto: ProyectoReporte, puntaje: float) -> ProyectoConsolidado:
    """Fila del reporte con el puntaje, los promedios por criterio y el detalle."""
    return ProyectoConsolidado(
        proyecto_id=proyecto.proyecto_id,
        proyecto=proyecto.proyecto,
        equipo=proyecto.equipo,
        modalidad=proyecto.modalidad,
        feria=proyecto.feria,
        puntaje=puntaje,
        integrantes=proyecto.integrantes,
        asignaturas=tuple(a.nombre for a in proyecto.asignaturas),
        criterios=proyecto.criterios(),
        evaluaciones=proyecto.evaluaciones,
    )


def agrupar(consolidados: list[tuple[ProyectoReporte, ProyectoConsolidado]],
            agrupar_por: Agrupacion) -> tuple[GrupoReporte, ...]:
    """REQ-19: arma los grupos ordenados por nombre; dentro de cada grupo, los proyectos van
    del puntaje más alto al más bajo (y por nombre si empatan)."""
    grupos: dict[tuple[int, str], list[ProyectoConsolidado]] = {}
    for proyecto, fila in consolidados:
        for clave in _claves_de_grupo(proyecto, agrupar_por):
            grupos.setdefault(clave, []).append(fila)
    return tuple(
        GrupoReporte(id=grupo_id, nombre=nombre, proyectos=tuple(
            sorted(filas, key=lambda f: (-f.puntaje, f.proyecto))))
        for (grupo_id, nombre), filas in sorted(grupos.items(), key=lambda g: g[0][1]))


def medir_avance(proyectos: tuple[ProyectoReporte, ...]) -> AvanceEvaluacion:
    """Cuenta las evaluaciones por estado y los proyectos que no tienen evaluador."""
    estados = [e.estado for p in proyectos for e in p.evaluaciones]
    return AvanceEvaluacion(
        total=len(estados),
        confirmadas=estados.count(EstadoEvaluacion.CONFIRMADA),
        borradores=estados.count(EstadoEvaluacion.BORRADOR),
        sin_empezar=estados.count(EstadoEvaluacion.PENDIENTE),
        proyectos_sin_evaluador=sum(1 for p in proyectos if not p.evaluaciones),
    )


def como_pendiente(proyecto: ProyectoReporte) -> ProyectoPendiente:
    """Proyecto que no entra al reporte, con las evaluaciones que le faltan."""
    faltantes = tuple(e for e in proyecto.evaluaciones
                      if e.estado is not EstadoEvaluacion.CONFIRMADA)
    return ProyectoPendiente(
        proyecto_id=proyecto.proyecto_id,
        proyecto=proyecto.proyecto,
        equipo=proyecto.equipo,
        feria=proyecto.feria,
        confirmadas=len(proyecto.evaluaciones) - len(faltantes),
        total=len(proyecto.evaluaciones),
        faltantes=faltantes,
    )


class ReporteServicio:
    """Valida los filtros, consolida los puntajes y agrupa los proyectos de la feria."""

    def __init__(self, repositorio: ReporteRepositorio, reloj: Reloj) -> None:
        self._repo = repositorio
        self._reloj = reloj

    def _nombrar_filtros(self, filtros: FiltrosReporte) -> tuple[tuple[str, str], ...]:
        """Nombre de cada filtro aplicado; 404 si la feria, asignatura o programa no
        existe."""
        revisar = (
            ("Feria", filtros.feria_id, self._repo.nombre_feria,
             FeriaNoEncontradaError("La feria indicada no existe.")),
            ("Programa académico", filtros.programa_id, self._repo.nombre_programa,
             ProgramaNoEncontradoError("El programa académico indicado no existe.")),
            ("Asignatura", filtros.asignatura_id, self._repo.nombre_asignatura,
             AsignaturaNoEncontradaError("La asignatura indicada no existe.")),
        )
        aplicados = []
        for etiqueta, identificador, buscar_nombre, error in revisar:
            if identificador is None:                                        # D2
                continue
            nombre = buscar_nombre(identificador)
            if nombre is None:                                               # D3
                raise error
            aplicados.append((etiqueta, nombre))
        return tuple(aplicados)

    def generar(self, parametros: Mapping[str, str]) -> Reporte:
        """400 si un filtro es inválido, 404 si lo que se filtra no existe.

        Solo entran los proyectos con todas sus evaluaciones confirmadas (REQ-18); los
        demás quedan en la lista de pendientes con lo que les falta.
        """
        filtros = leer_filtros(parametros)                                   # D1
        aplicados = self._nombrar_filtros(filtros)
        proyectos = self._repo.proyectos_para_reporte(
            filtros.feria_id, filtros.asignatura_id, filtros.programa_id)
        consolidados, pendientes = [], []
        for proyecto in proyectos:                                           # D4
            puntaje = proyecto.puntaje_consolidado()
            if puntaje is None:                                              # D5
                pendientes.append(como_pendiente(proyecto))
            else:
                consolidados.append((proyecto, consolidar(proyecto, puntaje)))
        puntajes = [fila.puntaje for _, fila in consolidados]
        return Reporte(
            filtros=filtros,
            filtros_aplicados=aplicados,
            generado=self._reloj.ahora(),
            grupos=agrupar(consolidados, filtros.agrupar_por),
            consolidados=len(consolidados),
            promedio_general=(round(sum(puntajes) / len(puntajes), 2)
                              if puntajes else None),                        # D6
            distribucion=Distribucion.de_puntajes(puntajes),
            avance=medir_avance(proyectos),
            pendientes=tuple(pendientes),
        )
