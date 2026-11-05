"""HU-010 · ``GET /api/reportes`` contra la base temporal.

Además de los datos de demostración (proyecto 1, del docente 1, en la feria 1), la fixture
``feria_evaluada`` agrega:

- Un segundo docente (3), el programa 2 con la asignatura 4 y la feria 2.
- Proyecto 2 «Robot» (PIA, asignaturas 1 y 2): confirmado por los docentes 1 y 3 con 4.0 y 3.0.
- Proyecto 3 «Inventario» (asignatura 2): confirmado por el docente 1, en borrador por el 3.
- Proyecto 4 «Sin evaluar» (asignatura 2): sin evaluadores.
- Proyecto 5 «Medidor» (feria 2, asignatura 4): confirmado por el docente 3 con 4.8.

El proyecto 1 se califica por la API (4, 3, 5 → 3.9), igual que en HU-007.
"""

import time

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
            INSERT INTO evaluacion (proyecto_id, evaluador_id, estado, puntaje_final) VALUES
                (2, 1, 'CONFIRMADA', 4.0), (2, 3, 'CONFIRMADA', 3.0),
                (3, 1, 'CONFIRMADA', 4.5), (3, 3, 'BORRADOR', 2.0),
                (5, 3, 'CONFIRMADA', 4.8);
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
    assert (robot["modalidad"], robot["evaluaciones"], robot["equipo"]) == ("PIA", 2, "Equipo Demo")


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


@pytest.mark.parametrize("rol, estado", [
    pytest.param(None, 401, id="sin-sesion"),
    pytest.param("EVALUADOR", 403, id="evaluador"),
    pytest.param("ESTUDIANTE", 403, id="estudiante"),
])
def test_solo_el_administrador_genera_reportes(cliente_como, rol, estado):
    """RNF-03: el reporte es del administrador (actor de HU-010)."""
    assert cliente_como(rol).get(URL).status_code == estado


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
