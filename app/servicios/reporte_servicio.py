"""Caso de uso HU-010: consolidar y generar reportes de resultados (REQ-18, REQ-19)."""

from collections.abc import Mapping

from app.dominio.errores import (
    AsignaturaNoEncontradaError,
    FeriaNoEncontradaError,
    ProgramaNoEncontradoError,
)
from app.dominio.modelos import (
    Agrupacion,
    FiltrosReporte,
    GrupoReporte,
    ProyectoConsolidado,
    ProyectoReporte,
    Reporte,
)
from app.repositorios.contratos import ReporteRepositorio
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


def agrupar(consolidados: list[tuple[ProyectoReporte, float]],
            agrupar_por: Agrupacion) -> tuple[GrupoReporte, ...]:
    """REQ-19: arma los grupos ordenados por nombre; dentro de cada grupo, los proyectos van
    del puntaje más alto al más bajo (y por nombre si empatan)."""
    grupos: dict[tuple[int, str], list[ProyectoConsolidado]] = {}
    for proyecto, puntaje in consolidados:
        fila = ProyectoConsolidado(
            proyecto_id=proyecto.proyecto_id,
            proyecto=proyecto.proyecto,
            equipo=proyecto.equipo,
            modalidad=proyecto.modalidad,
            feria=proyecto.feria,
            puntaje=puntaje,
            evaluaciones=len(proyecto.evaluaciones),
        )
        for clave in _claves_de_grupo(proyecto, agrupar_por):
            grupos.setdefault(clave, []).append(fila)
    return tuple(
        GrupoReporte(id=grupo_id, nombre=nombre, proyectos=tuple(
            sorted(filas, key=lambda f: (-f.puntaje, f.proyecto))))
        for (grupo_id, nombre), filas in sorted(grupos.items(), key=lambda g: g[0][1]))


class ReporteServicio:
    """Valida los filtros, consolida los puntajes y agrupa los proyectos de la feria."""

    def __init__(self, repositorio: ReporteRepositorio) -> None:
        self._repo = repositorio

    def _verificar_que_existan(self, filtros: FiltrosReporte) -> None:
        """404 si se filtra por una feria, asignatura o programa que no existe."""
        if filtros.feria_id is not None and not self._repo.existe_feria(
                filtros.feria_id):                                           # D2
            raise FeriaNoEncontradaError("La feria indicada no existe.")
        if filtros.asignatura_id is not None and not self._repo.existe_asignatura(
                filtros.asignatura_id):                                      # D3
            raise AsignaturaNoEncontradaError("La asignatura indicada no existe.")
        if filtros.programa_id is not None and not self._repo.existe_programa(
                filtros.programa_id):                                        # D4
            raise ProgramaNoEncontradoError("El programa académico indicado no existe.")

    def generar(self, parametros: Mapping[str, str]) -> Reporte:
        """400 si un filtro es inválido, 404 si lo que se filtra no existe.

        Solo entran los proyectos con todas sus evaluaciones confirmadas (REQ-18); los
        demás se cuentan como pendientes.
        """
        filtros = leer_filtros(parametros)                                   # D1
        self._verificar_que_existan(filtros)
        proyectos = self._repo.proyectos_para_reporte(
            filtros.feria_id, filtros.asignatura_id, filtros.programa_id)
        consolidados = []
        for proyecto in proyectos:                                           # D5
            puntaje = proyecto.puntaje_consolidado()
            if puntaje is not None:                                          # D6
                consolidados.append((proyecto, puntaje))
        promedio = (round(sum(p for _, p in consolidados) / len(consolidados), 2)
                    if consolidados else None)                               # D7
        return Reporte(
            filtros=filtros,
            grupos=agrupar(consolidados, filtros.agrupar_por),
            consolidados=len(consolidados),
            pendientes=len(proyectos) - len(consolidados),
            promedio_general=promedio,
        )
