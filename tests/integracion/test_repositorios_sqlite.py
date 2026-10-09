"""Repositorios contra una base SQLite temporal (``tmp_path``).

Comprueban lo que un mock no puede: que la restricción UNIQUE realmente
rechaza el duplicado, que la transacción se deshace completa y que un error
de integridad distinto termina en ``ErrorPersistencia``.
"""

from datetime import date

import pytest

from app.dominio.errores import ConflictoUnicidadError, ErrorPersistencia
from app.dominio.modelos import Modalidad, Proyecto, Rol, Usuario
from app.repositorios.sqlite_repositorios import (
    SqliteFeriaRepositorio,
    SqliteInstitucionRepositorio,
    SqliteProyectoRepositorio,
    SqliteRubricaRepositorio,
    SqliteUsuarioRepositorio,
)


def contar(conexion, tabla):
    """Número de filas de una tabla."""
    return conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]


def test_listar_dominios_devuelve_minusculas(conexion):
    """Los dominios se comparan siempre en minúsculas."""
    assert SqliteInstitucionRepositorio(conexion).listar_dominios() == \
        frozenset({"pascualbravo.edu.co"})


def test_correo_duplicado_lanza_conflicto_y_no_deja_filas_huerfanas(conexion):
    """El INSERT duplicado falla y la transacción se deshace completa."""
    repo = SqliteUsuarioRepositorio(conexion)
    usuario = Usuario(None, "Ana", "ana@pascualbravo.edu.co", Rol.ESTUDIANTE, 1, (1, 2))
    repo.guardar(usuario)
    usuarios, asignaturas = contar(conexion, "usuario"), contar(conexion, "usuario_asignatura")
    with pytest.raises(ConflictoUnicidadError):
        repo.guardar(usuario)
    assert contar(conexion, "usuario") == usuarios
    assert contar(conexion, "usuario_asignatura") == asignaturas


def test_error_de_integridad_distinto_a_unique_es_error_de_persistencia(conexion):
    """Una clave foránea inválida (programa 999) no es un duplicado: es un 500."""
    repo = SqliteUsuarioRepositorio(conexion)
    with pytest.raises(ErrorPersistencia):
        repo.guardar(Usuario(None, "Ana", "ana@pascualbravo.edu.co", Rol.ESTUDIANTE, 999))
    assert not repo.existe_correo("ana@pascualbravo.edu.co")


def test_proyecto_duplicado_en_la_misma_feria_lanza_conflicto(conexion):
    """UNIQUE (feria_id, equipo_id, nombre_normalizado) es la segunda barrera de RN002."""
    repo = SqliteProyectoRepositorio(conexion)
    proyecto = Proyecto(None, 1, 1, "Robot", "", Modalidad.PA, (1,), date(2026, 10, 9))
    repo.registrar(proyecto, "robot")
    with pytest.raises(ConflictoUnicidadError):
        repo.registrar(proyecto, "robot")
    assert repo.existe_en_feria(1, "robot", 1)


def test_feria_y_rubrica_se_leen_con_sus_relaciones(conexion):
    """La feria trae sus asignaturas y la rúbrica sus criterios en orden."""
    feria = SqliteFeriaRepositorio(conexion).obtener(1)
    rubrica = SqliteRubricaRepositorio(conexion).obtener_por_feria(1)
    assert feria.asignatura_ids == frozenset({1, 2})
    assert feria.fecha_fin == date(2026, 12, 31)
    assert [c.peso for c in rubrica.criterios] == [0.5, 0.3, 0.2]
    assert SqliteFeriaRepositorio(conexion).obtener(999) is None
    assert SqliteRubricaRepositorio(conexion).obtener_por_feria(999) is None
