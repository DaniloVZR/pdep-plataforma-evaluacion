"""HU-005 · Caminos de ``InscripcionServicio.inscribir``. V(G) = 9.

El reloj es falso (``reloj_fijo``), así que los límites del plazo se prueban
con fechas exactas sin depender del día en que corren las pruebas.
"""

from dataclasses import replace
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.dominio.errores import (
    AsignaturaNoParticipanteError,
    ConflictoUnicidadError,
    DatoInvalidoError,
    EquipoNoEncontradoError,
    FeriaNoEncontradaError,
    InscripcionNoAbiertaError,
    PlazoVencidoError,
    ProyectoDuplicadoError,
)
from app.dominio.modelos import Feria, Modalidad
from app.repositorios.contratos import EquipoRepositorio, FeriaRepositorio, ProyectoRepositorio
from app.servicios.inscripcion_servicio import InscripcionServicio

INICIO = date(2026, 10, 1)
FIN = date(2026, 10, 15)
FERIA = Feria(id=7, nombre="Feria 2026-2", fecha_inicio=INICIO, fecha_fin=FIN,
              asignatura_ids=frozenset({1, 2, 3}))


@pytest.fixture(name="repos")
def fixture_repos():
    """Repositorios simulados configurados para el camino exitoso."""
    equipo_repo = Mock(spec=EquipoRepositorio)
    equipo_repo.existe.return_value = True
    feria_repo = Mock(spec=FeriaRepositorio)
    feria_repo.obtener.return_value = FERIA
    proyecto_repo = Mock(spec=ProyectoRepositorio)
    proyecto_repo.existe_en_feria.return_value = False
    proyecto_repo.registrar.side_effect = lambda proyecto, _nombre: replace(proyecto, id=50)
    return SimpleNamespace(equipo=equipo_repo, feria=feria_repo, proyecto=proyecto_repo)


@pytest.fixture(name="crear_servicio")
def fixture_crear_servicio(repos, reloj_fijo):
    """Fábrica: servicio cuyo reloj marca la fecha indicada."""
    def crear(hoy: date = date(2026, 10, 9)) -> InscripcionServicio:
        return InscripcionServicio(repos.equipo, repos.feria, repos.proyecto, reloj_fijo(hoy))
    return crear


@pytest.fixture(name="datos")
def fixture_datos():
    """Solicitud válida de un Proyecto Integrador."""
    return {"equipo_id": 3, "feria_id": 7, "nombre": "Robot Clasificador",
            "descripcion": "Clasifica residuos", "modalidad": "PIA", "asignatura_ids": [1, 2]}


def test_c1_datos_invalidos(crear_servicio, repos, datos):
    """C1: 1→2→3→23→24. PIA con una sola asignatura incumple RN009."""
    datos["asignatura_ids"] = [1]
    with pytest.raises(DatoInvalidoError):
        crear_servicio().inscribir(datos)
    repos.equipo.existe.assert_not_called()


def test_c2_equipo_inexistente(crear_servicio, repos, datos):
    """C2: 1→2→4→5→23→24."""
    repos.equipo.existe.return_value = False
    with pytest.raises(EquipoNoEncontradoError):
        crear_servicio().inscribir(datos)
    repos.feria.obtener.assert_not_called()


def test_c3_feria_inexistente(crear_servicio, repos, datos):
    """C3: 1→2→4→6→7→8→23→24. ``feria_repo.obtener`` devuelve ``None``."""
    repos.feria.obtener.return_value = None
    with pytest.raises(FeriaNoEncontradaError):
        crear_servicio().inscribir(datos)
    repos.proyecto.registrar.assert_not_called()


def test_c4_asignatura_no_participa(crear_servicio, repos, datos):
    """C4: 1→2→4→6→7→9→10→23→24. La asignatura 9 no está en la feria."""
    datos["asignatura_ids"] = [1, 9]
    with pytest.raises(AsignaturaNoParticipanteError):
        crear_servicio().inscribir(datos)
    repos.proyecto.registrar.assert_not_called()


def test_c5_un_dia_antes_del_inicio(crear_servicio, repos, datos):
    """C5: 1→2→4→6→7→9→11→12→13→23→24. hoy = 30/09 (inicio − 1)."""
    with pytest.raises(InscripcionNoAbiertaError):
        crear_servicio(date(2026, 9, 30)).inscribir(datos)
    repos.proyecto.existe_en_feria.assert_not_called()


def test_c6_un_dia_despues_del_fin(crear_servicio, repos, datos):
    """C6: 1→2→4→6→7→9→11→12→14→15→23→24. hoy = 16/10 (fin + 1)."""
    with pytest.raises(PlazoVencidoError):
        crear_servicio(date(2026, 10, 16)).inscribir(datos)
    repos.proyecto.existe_en_feria.assert_not_called()


def test_c7_proyecto_duplicado(crear_servicio, repos, datos):
    """C7: 1→2→4→6→7→9→11→12→14→16→17→18→23→24 (RN002)."""
    repos.proyecto.existe_en_feria.return_value = True
    with pytest.raises(ProyectoDuplicadoError):
        crear_servicio().inscribir(datos)
    repos.proyecto.registrar.assert_not_called()


def test_c8_conflicto_de_unicidad_al_registrar(crear_servicio, repos, datos):
    """C8: 1→2→4→6→7→9→11→12→14→16→17→19→20→21→23→24.

    La consulta previa no vio el duplicado, pero la restricción UNIQUE de la
    base de datos sí (dos solicitudes simultáneas, RNF-02).
    """
    repos.proyecto.registrar.side_effect = ConflictoUnicidadError("UNIQUE constraint failed")
    with pytest.raises(ProyectoDuplicadoError):
        crear_servicio().inscribir(datos)


def test_c9_inscripcion_exitosa(crear_servicio, repos, datos):
    """C9: 1→2→4→6→7→9→11→12→14→16→17→19→20→22→24."""
    datos["nombre"] = "  Robot   Clasificador "
    proyecto = crear_servicio().inscribir(datos)
    assert proyecto.id == 50
    assert proyecto.nombre == "Robot Clasificador"
    assert proyecto.modalidad is Modalidad.PIA
    assert proyecto.asignatura_ids == (1, 2)
    assert proyecto.fecha_inscripcion == date(2026, 10, 9)
    repos.proyecto.existe_en_feria.assert_called_once_with(3, "robot clasificador", 7)


@pytest.mark.parametrize("hoy", [
    pytest.param(INICIO, id="primer-dia"),
    pytest.param(FIN, id="ultimo-dia"),
])
def test_los_dos_dias_limite_son_validos(crear_servicio, datos, hoy):
    """Valores frontera de D5 y D6: ``hoy == fecha_inicio`` y ``hoy == fecha_fin``."""
    assert crear_servicio(hoy).inscribir(datos).fecha_inscripcion == hoy
