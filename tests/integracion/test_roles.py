"""RNF-03 · La API revisa la sesión y el rol en cada petición (PDEP-47).

Cuentas de app/datos_demo.sql: evaluador = docente 1 y estudiante = usuario 2.
Los casos CP-10, CP-21, CP-33 y CP-34 del RTF4 se prueban aquí contra la API.
"""

import pytest

from app import seguridad

NUEVO_USUARIO = {"nombres": "Ana", "correo": "ana@pascualbravo.edu.co", "rol": "ESTUDIANTE",
                 "programa_id": 1, "asignatura_ids": [1]}
NUEVO_PROYECTO = {"equipo_id": 1, "feria_id": 1, "nombre": "Robot", "modalidad": "PIA",
                  "asignatura_ids": [1, 2]}
CALIFICACION = {"evaluador_id": 1, "notas": {"1": 4.0, "2": 3.0, "3": 5.0}}

PETICIONES = {
    "registrar usuario": ("post", "/api/usuarios", NUEVO_USUARIO),
    "inscribir proyecto": ("post", "/api/proyectos", NUEVO_PROYECTO),
    "calificar": ("put", "/api/proyectos/1/evaluacion", CALIFICACION),
    "listar ferias": ("get", "/api/ferias", None),
    "consultar resultados": ("get", "/api/resultados?estudiante_id=2", None),
}


def _enviar(cliente, nombre):
    metodo, url, cuerpo = PETICIONES[nombre]
    return getattr(cliente, metodo)(url, json=cuerpo) if cuerpo else getattr(cliente, metodo)(url)


@pytest.mark.parametrize("nombre", list(PETICIONES))
def test_cp34_sin_sesion_responde_401(cliente_como, nombre):
    """Sin token ningún endpoint hace cambios ni muestra datos."""
    respuesta = _enviar(cliente_como(None), nombre)
    assert respuesta.status_code == 401
    assert respuesta.get_json()["codigo"] == "sesion_requerida"


@pytest.mark.parametrize("encabezado", [
    pytest.param("Bearer token-inventado", id="token-alterado"),
    pytest.param("token-sin-bearer", id="sin-bearer"),
    pytest.param("Bearer ", id="bearer-vacio"),
])
def test_token_invalido_responde_401(cliente_como, encabezado):
    """Un token que no firmó el servidor no sirve, aunque tenga la forma correcta."""
    respuesta = cliente_como(None).get("/api/ferias", headers={"Authorization": encabezado})
    assert respuesta.status_code == 401


def test_token_vencido_responde_401(cliente_como, monkeypatch):
    """Pasadas las horas de la sesión el token deja de servir."""
    cliente = cliente_como("ESTUDIANTE")
    monkeypatch.setattr(seguridad, "HORAS_SESION", -1)
    assert cliente.get("/api/ferias").status_code == 401


@pytest.mark.parametrize("rol, nombre", [
    pytest.param("ESTUDIANTE", "registrar usuario", id="CP-10-estudiante"),
    pytest.param("EVALUADOR", "registrar usuario", id="CP-10-evaluador"),
    pytest.param("EVALUADOR", "inscribir proyecto", id="CP-21"),
    pytest.param("ESTUDIANTE", "calificar", id="CP-33"),
    pytest.param("EVALUADOR", "consultar resultados", id="evaluador-resultados"),
])
def test_rol_que_no_corresponde_responde_403(cliente_como, rol, nombre):
    """Con sesión pero con otro rol: 403 y no se guarda nada."""
    respuesta = _enviar(cliente_como(rol), nombre)
    assert respuesta.status_code == 403
    assert respuesta.get_json()["codigo"] == "sin_permiso"


@pytest.mark.parametrize("url, rol", [
    pytest.param("/api/instituciones", "EVALUADOR", id="instituciones"),
    pytest.param("/api/facultades", "ESTUDIANTE", id="facultades"),
    pytest.param("/api/departamentos", "EVALUADOR", id="departamentos"),
    pytest.param("/api/programas", "ESTUDIANTE", id="programas"),
    pytest.param("/api/asignaturas", "EVALUADOR", id="asignaturas"),
    pytest.param("/api/ferias", "ESTUDIANTE", id="ferias"),
    pytest.param("/api/proyectos/1/evaluadores", "EVALUADOR", id="asignar-evaluadores"),
])
def test_registros_del_administrador_rechazan_otros_roles(cliente_como, url, rol):
    """Lo que solo hace el administrador se rechaza antes de leer los datos."""
    assert cliente_como(rol).post(url, json={}).status_code == 403


def test_usuario_no_registrado_por_estudiante(cliente_como):
    """CP-10: después del 403 el correo sigue libre y el administrador lo puede registrar."""
    assert _enviar(cliente_como("ESTUDIANTE"), "registrar usuario").status_code == 403
    assert _enviar(cliente_como("ADMINISTRADOR"), "registrar usuario").status_code == 201


def test_cada_rol_hace_lo_suyo(cliente_como):
    """El estudiante inscribe, el evaluador califica y los dos consultan lo propio."""
    assert _enviar(cliente_como("ESTUDIANTE"), "inscribir proyecto").status_code == 201
    assert _enviar(cliente_como("ESTUDIANTE"), "consultar resultados").status_code == 200
    evaluador = cliente_como("EVALUADOR")
    assert _enviar(evaluador, "calificar").status_code == 200
    assert evaluador.get("/api/evaluaciones?evaluador_id=1").status_code == 200


@pytest.mark.parametrize("rol, metodo, url, cuerpo", [
    pytest.param("EVALUADOR", "put", "/api/proyectos/1/evaluacion",
                 {**CALIFICACION, "evaluador_id": 2}, id="calificar-por-otro"),
    pytest.param("EVALUADOR", "get", "/api/evaluaciones?evaluador_id=2", None,
                 id="evaluaciones-de-otro"),
    pytest.param("ESTUDIANTE", "get", "/api/resultados?estudiante_id=3", None,
                 id="resultados-de-otro"),
])
def test_nadie_actua_en_nombre_de_otro(cliente_como, rol, metodo, url, cuerpo):
    """Un evaluador o un estudiante solo usa su propio id, aunque tenga el rol correcto."""
    enviar = getattr(cliente_como(rol), metodo)
    respuesta = enviar(url, json=cuerpo) if cuerpo else enviar(url)
    assert respuesta.status_code == 403
    assert respuesta.get_json()["codigo"] == "sin_permiso"


def test_evaluador_con_id_invalido_recibe_el_400_de_siempre(cliente_como):
    """Si el evaluador_id no es un entero, decide el validador de HU-007 (no el control de rol)."""
    respuesta = cliente_como("EVALUADOR").put("/api/proyectos/1/evaluacion",
                                              json={**CALIFICACION, "evaluador_id": "1"})
    assert respuesta.status_code == 400


def test_evaluador_con_cuerpo_que_no_es_json_recibe_400(cliente_como):
    """Sin JSON no hay evaluador_id que comparar: responde el validador de HU-007."""
    respuesta = cliente_como("EVALUADOR").put("/api/proyectos/1/evaluacion", data="hola",
                                              content_type="text/plain")
    assert respuesta.status_code == 400
