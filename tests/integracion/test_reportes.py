"""HU-010 · ``GET /api/reportes`` contra la base temporal.

Además de los datos de demostración (proyecto 1, del docente 1, en la feria 1), la fixture
``feria_evaluada`` agrega:

- Un segundo docente (3), el programa 2 con la asignatura 4 y la feria 2.
- Proyecto 2 «Robot» (PIA, asignaturas 1 y 2): confirmado por los docentes 1 y 3 con 4.0 y 3.0,
  con sus notas por criterio y la retroalimentación del docente 1.
- Proyecto 3 «Inventario» (asignatura 2): confirmado por el docente 1, en borrador por el 3.
- Proyecto 4 «Sin evaluar» (asignatura 2): sin evaluadores.
- Proyecto 5 «Medidor» (feria 2, asignatura 4): confirmado por el docente 3 con 4.8.

El proyecto 1 se califica por la API (4, 3, 5 → 3.9), igual que en HU-007.
"""

from io import BytesIO
import time

from openpyxl import load_workbook
import pytest

from app.db import abrir_conexion

URL = "/api/reportes"


@pytest.fixture(name="feria_evaluada")
def fixture_feria_evaluada(ruta_bd, cliente):
    """Carga los proyectos descritos arriba y confirma el proyecto 1 por la API."""
    conexion = abrir_conexion(ruta_bd)
    with conexion:
        conexion.executescript("""
            INSERT INTO usuario (id, nombres, correo, rol, programa_id) VALUES
                (3, 'Docente Dos', 'docente2@pascualbravo.edu.co', 'DOCENTE', 1);
            INSERT INTO programa (id, institucion_id, facultad_id, codigo, nombre) VALUES
                (2, 1, 1, 'IE', 'Ingeniería Eléctrica');
            INSERT INTO asignatura (id, programa_id, codigo, nombre, semestre) VALUES
                (4, 2, 'CIR', 'Circuitos', 3);
            INSERT INTO feria (id, institucion_id, nombre, fecha_inicio, fecha_fin) VALUES
                (2, 1, 'Feria de Proyectos 2026-1', '2026-01-01', '2026-06-30');
            INSERT INTO proyecto (id, equipo_id, feria_id, nombre, nombre_normalizado,
                                  modalidad, fecha_inscripcion) VALUES
                (2, 1, 1, 'Robot', 'robot', 'PIA', '2026-10-02'),
                (3, 1, 1, 'Inventario', 'inventario', 'PA', '2026-10-02'),
                (4, 1, 1, 'Sin evaluar', 'sin evaluar', 'PA', '2026-10-02'),
                (5, 1, 2, 'Medidor', 'medidor', 'PA', '2026-03-02');
            INSERT INTO proyecto_asignatura (proyecto_id, asignatura_id) VALUES
                (2, 1), (2, 2), (3, 2), (4, 2), (5, 4);
            INSERT INTO evaluacion (id, proyecto_id, evaluador_id, estado, puntaje_final,
                                    retroalimentacion) VALUES
                (2, 2, 1, 'CONFIRMADA', 4.0, 'Buen prototipo'), (3, 2, 3, 'CONFIRMADA', 3.0, ''),
                (4, 3, 1, 'CONFIRMADA', 4.5, ''), (5, 3, 3, 'BORRADOR', 2.0, ''),
                (6, 5, 3, 'CONFIRMADA', 4.8, '');
            INSERT INTO calificacion_criterio (evaluacion_id, criterio_id, nota) VALUES
                (2, 1, 4), (2, 2, 4), (2, 3, 4), (3, 1, 2), (3, 2, 4), (3, 3, 4);
        """)
    conexion.close()
    respuesta = cliente.put("/api/proyectos/1/evaluacion", json={
        "evaluador_id": 1, "notas": {"1": 4, "2": 3, "3": 5}, "confirmar": True})
    assert respuesta.status_code == 200


def grupos(reporte):
    """``[(grupo, [(proyecto, puntaje), ...]), ...]``."""
    return [(g["nombre"], [(p["proyecto"], p["puntaje"]) for p in g["proyectos"]])
            for g in reporte["grupos"]]


@pytest.mark.usefixtures("feria_evaluada")
def test_reporte_por_feria_solo_con_evaluaciones_confirmadas(cliente):
    """Criterio 1 y REQ-18: Inventario (borrador) y Sin evaluar no entran; Robot promedia."""
    respuesta = cliente.get(URL)
    assert respuesta.status_code == 200
    reporte = respuesta.get_json()
    assert reporte["agrupar_por"] == "feria"
    assert reporte["resumen"] == {"proyectos_consolidados": 3, "proyectos_pendientes": 2,
                                  "promedio_general": 4.07}
    assert grupos(reporte) == [
        ("Feria de Proyectos 2026-1", [("Medidor", 4.8)]),
        ("Feria de Proyectos 2026-2", [("Proyecto Demo", 3.9), ("Robot", 3.5)]),
    ]
    feria_1 = reporte["grupos"][1]
    assert (feria_1["cantidad"], feria_1["promedio"], feria_1["maximo"],
            feria_1["minimo"]) == (2, 3.7, 3.9, 3.5)
    robot = feria_1["proyectos"][1]
    assert (robot["modalidad"], robot["equipo"], robot["nivel"]) == ("PIA", "Equipo Demo",
                                                                     "ACEPTABLE")


@pytest.mark.usefixtures("feria_evaluada")
@pytest.mark.parametrize("consulta, esperado", [
    pytest.param("?agrupar_por=asignatura", [
        ("Bases de Datos II", [("Robot", 3.5)]),
        ("Circuitos", [("Medidor", 4.8)]),
        ("Ingeniería de Software II", [("Proyecto Demo", 3.9), ("Robot", 3.5)]),
    ], id="por-asignatura"),
    pytest.param("?agrupar_por=programa", [
        ("Ingeniería Eléctrica", [("Medidor", 4.8)]),
        ("Tecnología en Desarrollo de Software", [("Proyecto Demo", 3.9), ("Robot", 3.5)]),
    ], id="por-programa"),
    pytest.param("?feria_id=2", [
        ("Feria de Proyectos 2026-1", [("Medidor", 4.8)]),
    ], id="filtro-feria"),
    pytest.param("?programa_id=2&agrupar_por=programa", [
        ("Ingeniería Eléctrica", [("Medidor", 4.8)]),
    ], id="filtro-programa"),
    pytest.param("?asignatura_id=2&agrupar_por=asignatura", [
        ("Bases de Datos II", [("Robot", 3.5)]),
    ], id="filtro-asignatura-sin-la-otra-del-pia"),
    pytest.param("?feria_id=1&programa_id=2", [], id="filtros-sin-resultados"),
])
def test_agrupar_y_filtrar(cliente, consulta, esperado):
    """Criterio 2 y REQ-19: agrupa por feria, asignatura o programa y filtra por cada uno."""
    respuesta = cliente.get(URL + consulta)
    assert respuesta.status_code == 200
    assert grupos(respuesta.get_json()) == esperado


@pytest.mark.usefixtures("feria_evaluada")
def test_filtro_por_asignatura_cuenta_sus_pendientes(cliente):
    """En la asignatura 2 solo entra Robot; Inventario y Sin evaluar quedan pendientes."""
    reporte = cliente.get(URL + "?asignatura_id=2").get_json()
    assert reporte["filtros"] == {"feria_id": None, "asignatura_id": 2, "programa_id": None}
    assert [p["proyecto"] for p in reporte["pendientes"]] == ["Inventario", "Sin evaluar"]
    assert reporte["resumen"] == {"proyectos_consolidados": 1, "proyectos_pendientes": 2,
                                  "promedio_general": 3.5}


def test_proyecto_entra_al_confirmar_su_evaluacion(cliente):
    """Con los datos de demostración el proyecto 1 está pendiente hasta que se confirma."""
    antes = cliente.get(URL).get_json()
    assert (antes["grupos"], antes["resumen"]["proyectos_pendientes"]) == ([], 1)
    cliente.put("/api/proyectos/1/evaluacion", json={
        "evaluador_id": 1, "notas": {"1": 4, "2": 3, "3": 5}, "confirmar": False})
    assert cliente.get(URL).get_json()["grupos"] == []          # el borrador no cuenta
    cliente.put("/api/proyectos/1/evaluacion", json={
        "evaluador_id": 1, "notas": {"1": 4, "2": 3, "3": 5}, "confirmar": True})
    assert grupos(cliente.get(URL).get_json()) == [
        ("Feria de Proyectos 2026-2", [("Proyecto Demo", 3.9)])]


@pytest.mark.parametrize("consulta, estado, codigo", [
    pytest.param("?feria_id=99", 404, "feria_no_encontrada", id="feria"),
    pytest.param("?asignatura_id=99", 404, "asignatura_no_encontrada", id="asignatura"),
    pytest.param("?programa_id=99", 404, "programa_no_encontrado", id="programa"),
    pytest.param("?feria_id=abc", 400, "dato_invalido", id="id-texto"),
    pytest.param("?agrupar_por=docente", 400, "dato_invalido", id="agrupacion"),
])
def test_filtros_invalidos(cliente, consulta, estado, codigo):
    """400 si el filtro está mal escrito; 404 si lo filtrado no existe."""
    respuesta = cliente.get(URL + consulta)
    assert respuesta.status_code == estado
    assert respuesta.get_json()["codigo"] == codigo


@pytest.mark.usefixtures("feria_evaluada")
def test_distribucion_avance_y_pendientes(cliente):
    """Distribución por nivel, avance de las evaluaciones y lo que falta de cada pendiente."""
    reporte = cliente.get(URL).get_json()
    assert reporte["distribucion"] == {"excelente": 1, "bueno": 0, "aceptable": 2,
                                       "insuficiente": 0, "aprobados": 3, "reprobados": 0}
    assert reporte["avance"] == {"total": 6, "confirmadas": 5, "borradores": 1,
                                 "sin_empezar": 0, "proyectos_sin_evaluador": 1,
                                 "porcentaje": 83.3}
    inventario, sin_evaluar = reporte["pendientes"]
    assert (inventario["confirmadas"], inventario["total"]) == (1, 2)
    assert [(f["evaluador"], f["estado"]) for f in inventario["faltantes"]] == [
        ("Docente Dos", "BORRADOR")]
    assert (sin_evaluar["total"], sin_evaluar["faltantes"]) == (0, [])
    assert reporte["generado"].startswith("20")


@pytest.mark.usefixtures("feria_evaluada")
def test_detalle_y_criterios_del_proyecto(cliente):
    """Integrantes, asignaturas, notas por criterio y retroalimentación de cada evaluador."""
    feria = cliente.get(URL + "?feria_id=1").get_json()["grupos"][0]
    robot = next(p for p in feria["proyectos"] if p["proyecto"] == "Robot")
    assert robot["integrantes"] == ["Estudiante Demo"]
    assert robot["asignaturas"] == ["Bases de Datos II", "Ingeniería de Software II"]
    assert [(c["criterio"], c["nota"]) for c in robot["criterios"]] == [
        ("Funcionalidad", 3.0), ("Calidad del código", 4.0), ("Presentación", 4.0)]
    assert [(e["evaluador"], e["puntaje_final"], e["retroalimentacion"])
            for e in robot["evaluaciones"]] == [("Docente Evaluador", 4.0, "Buen prototipo"),
                                                ("Docente Dos", 3.0, "")]
    # El grupo promedia los criterios de Robot y de Proyecto Demo (4, 3, 5).
    assert [(c["criterio"], c["nota"]) for c in feria["criterios"]] == [
        ("Funcionalidad", 3.5), ("Calidad del código", 3.5), ("Presentación", 4.5)]


@pytest.mark.usefixtures("feria_evaluada")
def test_excel_con_sus_cinco_hojas(cliente):
    """El Excel trae las mismas cifras que la pantalla, con los mismos filtros."""
    respuesta = cliente.get(URL + "/excel?agrupar_por=asignatura&feria_id=1")
    assert respuesta.status_code == 200
    assert respuesta.mimetype.endswith("spreadsheetml.sheet")
    assert 'filename="reporte-resultados-' in respuesta.headers["Content-Disposition"]
    libro = load_workbook(BytesIO(respuesta.data))
    assert libro.sheetnames == ["Resumen", "Resultados", "Por criterio", "Retroalimentación",
                                "Pendientes"]
    resumen = [fila for fila in libro["Resumen"].iter_rows(values_only=True) if fila[0]]
    assert ("Filtros", "Feria: Feria de Proyectos 2026-2") in [f[:2] for f in resumen]
    assert ("Proyectos con evaluación confirmada", 2) in [f[:2] for f in resumen]
    resultados = list(libro["Resultados"].iter_rows(values_only=True))
    assert resultados[0][-3:] == ("Funcionalidad", "Calidad del código", "Presentación")
    assert [(f[0], f[1], f[2], f[9]) for f in resultados[1:]] == [
        ("Bases de Datos II", 1, "Robot", 3.5),
        ("Ingeniería de Software II", 1, "Proyecto Demo", 3.9),
        ("Ingeniería de Software II", 2, "Robot", 3.5)]
    retro = list(libro["Retroalimentación"].iter_rows(values_only=True))[1:]
    assert len(retro) == 3                    # Robot sale una vez aunque esté en dos grupos
    pendientes = list(libro["Pendientes"].iter_rows(values_only=True))[1:]
    assert [(f[0], f[3], f[4], f[5]) for f in pendientes] == [
        ("Inventario", "1 de 2", "Docente Dos", "En borrador"),
        ("Sin evaluar", "0 de 0", "Sin evaluador asignado", None)]


def test_excel_vacio_y_filtro_invalido(cliente):
    """Sin proyectos confirmados el Excel se genera igual; con un filtro inválido, 400."""
    respuesta = cliente.get(URL + "/excel")
    assert respuesta.status_code == 200
    libro = load_workbook(BytesIO(respuesta.data))
    assert libro["Resultados"].max_row == 1
    assert cliente.get(URL + "/excel?feria_id=x").status_code == 400


@pytest.mark.parametrize("url", [URL, URL + "/excel"])
@pytest.mark.parametrize("rol, estado", [
    pytest.param(None, 401, id="sin-sesion"),
    pytest.param("EVALUADOR", 403, id="evaluador"),
    pytest.param("ESTUDIANTE", 403, id="estudiante"),
])
def test_solo_el_administrador_genera_reportes(cliente_como, url, rol, estado):
    """RNF-03: el reporte y el Excel son del administrador (actor de HU-010)."""
    assert cliente_como(rol).get(url).status_code == estado


def test_rnf01_consolida_500_proyectos_en_menos_de_5_segundos(ruta_bd, cliente):
    """RNF-01: una feria con 500 proyectos y dos evaluaciones confirmadas en cada uno."""
    conexion = abrir_conexion(ruta_bd)
    with conexion:
        conexion.execute("INSERT INTO usuario (id, nombres, correo, rol, programa_id) VALUES "
                         "(3, 'Docente Dos', 'docente2@pascualbravo.edu.co', 'DOCENTE', 1)")
        ids = range(100, 600)
        conexion.executemany(
            "INSERT INTO proyecto (id, equipo_id, feria_id, nombre, nombre_normalizado, "
            "modalidad, fecha_inscripcion) VALUES (?, 1, 1, ?, ?, 'PA', '2026-10-02')",
            [(i, f"Proyecto {i}", f"proyecto {i}") for i in ids])
        conexion.executemany(
            "INSERT INTO proyecto_asignatura (proyecto_id, asignatura_id) VALUES (?, 1)",
            [(i,) for i in ids])
        conexion.executemany(
            "INSERT INTO evaluacion (proyecto_id, evaluador_id, estado, puntaje_final) "
            "VALUES (?, ?, 'CONFIRMADA', ?)",
            [(i, docente, 3.0 + docente / 2) for i in ids for docente in (1, 3)])
    conexion.close()

    inicio = time.perf_counter()
    respuesta = cliente.get(URL + "?feria_id=1")
    duracion = time.perf_counter() - inicio

    assert respuesta.status_code == 200
    resumen = respuesta.get_json()["resumen"]
    assert (resumen["proyectos_consolidados"], resumen["proyectos_pendientes"]) == (500, 1)
    assert resumen["promedio_general"] == 4.0          # (3.5 + 4.5) / 2 en cada proyecto
    assert duracion < 5
