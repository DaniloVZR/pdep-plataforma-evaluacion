"""Exporta el reporte de resultados de HU-010 a Excel (.xlsx) con openpyxl.

Hojas:

- **Resumen**: fecha de generación, filtros, indicadores, distribución por nivel, avance de
  la evaluación y una fila por grupo.
- **Resultados**: un proyecto por fila con su puesto, detalle, puntaje, nivel y la nota
  promedio de cada criterio.
- **Por criterio**: promedio de cada criterio en cada grupo.
- **Retroalimentación**: lo que escribió cada evaluador de cada proyecto.
- **Pendientes**: proyectos que no entraron y las evaluaciones que les faltan.
"""

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from app.dominio.modelos import (
    EstadoEvaluacion,
    NivelDesempeno,
    NOTA_APROBATORIA,
    Reporte,
)

TIPO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

ETIQUETA_AGRUPACION = {"feria": "Feria", "asignatura": "Asignatura",
                       "programa": "Programa académico"}
ETIQUETA_NIVEL = {
    NivelDesempeno.EXCELENTE: ("Excelente", "4.50 a 5.00"),
    NivelDesempeno.BUENO: ("Bueno", "4.00 a 4.49"),
    NivelDesempeno.ACEPTABLE: ("Aceptable", "3.00 a 3.99"),
    NivelDesempeno.INSUFICIENTE: ("Insuficiente", "menos de 3.00"),
}
ETIQUETA_ESTADO = {EstadoEvaluacion.PENDIENTE: "Sin empezar",
                   EstadoEvaluacion.BORRADOR: "En borrador",
                   EstadoEvaluacion.CONFIRMADA: "Confirmada"}

_AZUL = "0A3D73"
_ENCABEZADO = Font(bold=True, color="FFFFFF")
_FONDO_ENCABEZADO = PatternFill("solid", fgColor=_AZUL)
_TITULO = Font(bold=True, size=14, color=_AZUL)
_SUBTITULO = Font(bold=True, size=11, color=_AZUL)
_NEGRITA = Font(bold=True)
_AJUSTAR = Alignment(wrap_text=True, vertical="top")
_NOTA = "0.00"


def nombre_archivo(reporte: Reporte) -> str:
    """``reporte-resultados-AAAA-MM-DD.xlsx`` con la fecha de generación."""
    return f"reporte-resultados-{reporte.generado:%Y-%m-%d}.xlsx"


def _tabla(hoja: Worksheet, fila: int, encabezados: list[str], filas: list[list],
           formatos: dict[int, str] | None = None) -> int:
    """Escribe una tabla desde ``fila`` y devuelve la fila siguiente a la última.

    ``formatos`` asigna un formato de número por índice de columna (desde 0).
    """
    for columna, texto in enumerate(encabezados, start=1):
        celda = hoja.cell(fila, columna, texto)
        celda.font, celda.fill = _ENCABEZADO, _FONDO_ENCABEZADO
    for valores in filas:
        fila += 1
        for columna, valor in enumerate(valores, start=1):
            celda = hoja.cell(fila, columna, valor)
            if formatos and columna - 1 in formatos:
                celda.number_format = formatos[columna - 1]
    return fila + 1


def _anchos(hoja: Worksheet, anchos: list[int]) -> None:
    for columna, ancho in enumerate(anchos, start=1):
        hoja.column_dimensions[get_column_letter(columna)].width = ancho


def _como_lista(hoja: Worksheet, columnas: int, filas: int) -> None:
    """Fija la fila de encabezados y agrega el filtro de Excel a toda la tabla."""
    hoja.freeze_panes = "A2"
    hoja.auto_filter.ref = f"A1:{get_column_letter(columnas)}{max(filas, 1) + 1}"


def _hoja_resumen(hoja: Worksheet, reporte: Reporte) -> None:
    hoja.title = "Resumen"
    hoja["A1"] = "Reporte de resultados · PDEP"
    hoja["A1"].font = _TITULO
    filtros = "; ".join(f"{etiqueta}: {nombre}"
                        for etiqueta, nombre in reporte.filtros_aplicados) or "Sin filtros"
    datos = [
        ("Generado", reporte.generado.strftime("%d/%m/%Y %H:%M")),
        ("Agrupado por", ETIQUETA_AGRUPACION[reporte.filtros.agrupar_por.value]),
        ("Filtros", filtros),
        ("Regla", "Solo entran los proyectos con todas sus evaluaciones confirmadas; "
                  "el puntaje es el promedio de sus evaluadores."),
    ]
    for fila, (etiqueta, valor) in enumerate(datos, start=2):
        hoja.cell(fila, 1, etiqueta).font = _NEGRITA
        hoja.cell(fila, 2, valor)

    fila = 7
    hoja.cell(fila, 1, "Indicadores").font = _SUBTITULO
    avance = reporte.avance
    fila = _tabla(hoja, fila + 1, ["Indicador", "Valor"], [
        ["Proyectos con evaluación confirmada", reporte.consolidados],
        ["Proyectos pendientes (no entran al reporte)", len(reporte.pendientes)],
        ["Promedio general", reporte.promedio_general],
        ["Evaluaciones confirmadas", f"{avance.confirmadas} de {avance.total} "
                                     f"({avance.porcentaje:.1f} %)"],
        ["Evaluaciones en borrador", avance.borradores],
        ["Evaluaciones sin empezar", avance.sin_empezar],
        ["Proyectos sin evaluador asignado", avance.proyectos_sin_evaluador],
    ], {1: _NOTA})

    hoja.cell(fila + 1, 1, "Distribución de notas").font = _SUBTITULO
    distribucion = reporte.distribucion
    cantidades = [distribucion.excelente, distribucion.bueno, distribucion.aceptable,
                  distribucion.insuficiente]
    total = max(reporte.consolidados, 1)
    fila = _tabla(hoja, fila + 2, ["Nivel", "Rango", "Proyectos", "% del total"], [
        [*ETIQUETA_NIVEL[nivel], cantidad, cantidad / total]
        for nivel, cantidad in zip(NivelDesempeno, cantidades)
    ] + [[f"Aprobados (≥ {NOTA_APROBATORIA:.1f})", "", distribucion.aprobados,
          distribucion.aprobados / total],
         ["Reprobados", "", distribucion.reprobados, distribucion.reprobados / total]],
        {3: "0.0%"})

    hoja.cell(fila + 1, 1, "Por grupo").font = _SUBTITULO
    _tabla(hoja, fila + 2, [
        ETIQUETA_AGRUPACION[reporte.filtros.agrupar_por.value], "Proyectos", "Promedio",
        "Máximo", "Mínimo", "Aprobados", "Reprobados"], [
        [g.nombre, len(g.proyectos), g.promedio, g.maximo, g.minimo,
         g.distribucion.aprobados, g.distribucion.reprobados] for g in reporte.grupos
    ], {2: _NOTA, 3: _NOTA, 4: _NOTA})
    _anchos(hoja, [42, 34, 12, 12, 12, 12, 12])


def _hoja_resultados(hoja: Worksheet, reporte: Reporte) -> None:
    criterios = list(dict.fromkeys(
        c.criterio for g in reporte.grupos for p in g.proyectos for c in p.criterios))
    encabezados = [ETIQUETA_AGRUPACION[reporte.filtros.agrupar_por.value], "Puesto",
                   "Proyecto", "Equipo", "Integrantes", "Modalidad", "Feria", "Asignaturas",
                   "Evaluadores", "Puntaje", "Nivel", "Resultado", *criterios]
    filas = []
    for grupo in reporte.grupos:
        for puesto, p in enumerate(grupo.proyectos, start=1):
            notas = {c.criterio: c.nota for c in p.criterios}
            filas.append([
                grupo.nombre, puesto, p.proyecto, p.equipo, ", ".join(p.integrantes),
                p.modalidad.value, p.feria, ", ".join(p.asignaturas),
                ", ".join(e.evaluador for e in p.evaluaciones), p.puntaje,
                ETIQUETA_NIVEL[p.nivel][0],
                "Aprobado" if p.puntaje >= NOTA_APROBATORIA else "Reprobado",
                *(notas.get(nombre) for nombre in criterios)])
    formatos = {i: _NOTA for i in range(9, len(encabezados)) if i not in (10, 11)}
    _tabla(hoja, 1, encabezados, filas, formatos)
    _como_lista(hoja, len(encabezados), len(filas))
    _anchos(hoja, [30, 8, 28, 18, 32, 11, 26, 32, 30, 10, 13, 12] + [16] * len(criterios))


def _hoja_criterios(hoja: Worksheet, reporte: Reporte) -> None:
    filas = [[g.nombre, c.criterio, c.peso, c.nota]
             for g in reporte.grupos for c in g.criterios]
    _tabla(hoja, 1, [ETIQUETA_AGRUPACION[reporte.filtros.agrupar_por.value], "Criterio",
                     "Peso", "Nota promedio"], filas, {2: "0%", 3: _NOTA})
    _como_lista(hoja, 4, len(filas))
    _anchos(hoja, [34, 28, 10, 15])


def _hoja_retroalimentacion(hoja: Worksheet, reporte: Reporte) -> None:
    # Un PIA aparece en varios grupos: su retroalimentación se escribe una sola vez.
    proyectos = {p.proyecto_id: p for g in reporte.grupos for p in g.proyectos}
    filas = [[p.proyecto, p.equipo, p.feria, e.evaluador, e.puntaje_final,
              e.fecha_confirmacion.strftime("%d/%m/%Y %H:%M") if e.fecha_confirmacion else "",
              e.retroalimentacion or "(sin comentarios)"]
             for p in proyectos.values() for e in p.evaluaciones]
    _tabla(hoja, 1, ["Proyecto", "Equipo", "Feria", "Evaluador", "Puntaje",
                     "Confirmada el", "Retroalimentación"], filas, {4: _NOTA})
    for fila in hoja.iter_rows(min_row=2, min_col=7, max_col=7):
        fila[0].alignment = _AJUSTAR
    _como_lista(hoja, 7, len(filas))
    _anchos(hoja, [28, 18, 26, 24, 10, 17, 70])


def _hoja_pendientes(hoja: Worksheet, reporte: Reporte) -> None:
    filas = []
    for p in reporte.pendientes:
        avance = f"{p.confirmadas} de {p.total}"
        if not p.faltantes:
            filas.append([p.proyecto, p.equipo, p.feria, avance, "Sin evaluador asignado",
                          ""])
        for e in p.faltantes:
            filas.append([p.proyecto, p.equipo, p.feria, avance, e.evaluador,
                          ETIQUETA_ESTADO[e.estado]])
    _tabla(hoja, 1, ["Proyecto", "Equipo", "Feria", "Confirmadas", "Falta el evaluador",
                     "Estado"], filas)
    _como_lista(hoja, 6, len(filas))
    _anchos(hoja, [28, 18, 26, 13, 28, 14])


def generar_excel(reporte: Reporte) -> bytes:
    """El reporte como archivo .xlsx, listo para enviarlo en la respuesta."""
    libro = Workbook()
    _hoja_resumen(libro.active, reporte)
    _hoja_resultados(libro.create_sheet("Resultados"), reporte)
    _hoja_criterios(libro.create_sheet("Por criterio"), reporte)
    _hoja_retroalimentacion(libro.create_sheet("Retroalimentación"), reporte)
    _hoja_pendientes(libro.create_sheet("Pendientes"), reporte)
    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()
