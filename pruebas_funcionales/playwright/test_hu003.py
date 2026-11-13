"""HU-003 · Registrar estudiante o docente (pantalla /usuarios/nuevo). RTF4 v2, sección 5."""

from playwright.sync_api import Page, expect

from conftest import FRONTEND, consultar_api, elegir_opcion, error_del_campo, iniciar_sesion

PROGRAMA = "Tecnología en Desarrollo de Software"


def abrir_registro(page: Page) -> None:
    iniciar_sesion(page, rol="administrador")
    page.goto(f"{FRONTEND}/usuarios/nuevo")
    expect(page.get_by_role("heading", name="Registrar usuario")).to_be_visible()


def llenar(page: Page, nombres: str, correo: str, programa: str | None = PROGRAMA) -> None:
    page.get_by_label("Nombres completos").fill(nombres)
    page.get_by_label("Correo institucional").fill(correo)
    if programa:
        page.get_by_label("Programa académico").select_option(label=programa)


def registrar(page: Page) -> None:
    page.get_by_role("button", name="Registrar usuario").click()


def test_cp01_registra_estudiante_muestra_aviso_verde(page: Page):
    abrir_registro(page)
    elegir_opcion(page, "Estudiante")
    llenar(page, "Ana Pérez", "ana.perez@pascualbravo.edu.co")
    page.get_by_label("Ingeniería de Software II").check()
    registrar(page)
    expect(page.get_by_role("status")).to_have_text(
        "Ana Pérez quedó registrado como estudiante con el correo "
        "ana.perez@pascualbravo.edu.co.")
    expect(page.get_by_label("Nombres completos")).to_have_value("")
    expect(page.get_by_label("Correo institucional")).to_have_value("")
    expect(page.get_by_label("Programa académico")).to_have_value("")


def test_cp02_registra_docente_muestra_aviso_verde(page: Page):
    abrir_registro(page)
    elegir_opcion(page, "Docente")
    llenar(page, "Luis Gómez", "luis.gomez@pascualbravo.edu.co")
    page.get_by_label("Ingeniería de Software II").check()
    page.get_by_label("Bases de Datos II").check()
    registrar(page)
    expect(page.get_by_role("status")).to_have_text(
        "Luis Gómez quedó registrado como docente con el correo "
        "luis.gomez@pascualbravo.edu.co.")


def test_cp04_nombres_vacios_marca_el_campo(page: Page, peticiones):
    abrir_registro(page)
    llenar(page, "", "maria.lopez@pascualbravo.edu.co")
    registrar(page)
    expect(page.get_by_label("Nombres completos")).to_have_attribute("aria-invalid", "true")
    expect(error_del_campo(page, "Nombres completos")).to_have_text(
        "Escribe los nombres de la persona.")
    expect(page.get_by_role("status")).to_have_count(0)
    assert "POST /api/usuarios" not in peticiones


def test_cp05_correo_vacio_marca_el_campo(page: Page, peticiones):
    abrir_registro(page)
    llenar(page, "María López", "")
    registrar(page)
    expect(page.get_by_label("Correo institucional")).to_have_attribute("aria-invalid", "true")
    expect(error_del_campo(page, "Correo institucional")).to_have_text(
        "Escribe el correo institucional.")
    assert "POST /api/usuarios" not in peticiones


def test_cp06_correo_sin_arroba_marca_el_campo(page: Page, peticiones):
    abrir_registro(page)
    llenar(page, "María López", "maria.lopezpascualbravo.edu.co")
    registrar(page)
    expect(page.get_by_label("Correo institucional")).to_have_attribute("aria-invalid", "true")
    expect(error_del_campo(page, "Correo institucional")).to_have_text(
        "El correo debe tener una @.")
    assert "POST /api/usuarios" not in peticiones


def test_cp07_sin_programa_marca_la_lista(page: Page, peticiones):
    abrir_registro(page)
    llenar(page, "María López", "maria.lopez@pascualbravo.edu.co", programa=None)
    registrar(page)
    expect(page.get_by_label("Programa académico")).to_have_attribute("aria-invalid", "true")
    expect(error_del_campo(page, "Programa académico")).to_have_text(
        "Elige el programa académico.")
    assert "POST /api/usuarios" not in peticiones


def test_cp08_correo_personal_muestra_recuadro_rojo(page: Page):
    abrir_registro(page)
    llenar(page, "Ana Pérez", "ana.perez@gmail.com")
    registrar(page)
    expect(page.get_by_role("alert")).to_have_text(
        "El correo no pertenece a una institución registrada.")
    expect(page.get_by_label("Nombres completos")).to_have_value("Ana Pérez")
    expect(page.get_by_label("Correo institucional")).to_have_value("ana.perez@gmail.com")
    correos = [u["correo"] for u in consultar_api(page, "administrador", "/api/usuarios")]
    assert "ana.perez@gmail.com" not in correos


def test_cp11_correo_repetido_muestra_recuadro_rojo(page: Page):
    abrir_registro(page)
    llenar(page, "Ana Pérez", "ana.perez@pascualbravo.edu.co")
    registrar(page)
    expect(page.get_by_role("alert")).to_have_text("Ya existe un usuario con ese correo.")
    correos = [u["correo"] for u in consultar_api(page, "administrador", "/api/usuarios")]
    assert correos.count("ana.perez@pascualbravo.edu.co") == 1


def test_cp15_estudiante_no_ve_registrar_usuario(page: Page):
    iniciar_sesion(page, rol="estudiante")
    page.goto(f"{FRONTEND}/usuarios/nuevo")
    expect(page).to_have_url(f"{FRONTEND}/proyectos/inscribir")
    expect(page.get_by_role("heading", name="Inscribir proyecto")).to_be_visible()
    expect(page.get_by_label("Nombres completos")).to_have_count(0)


def test_cp17_evaluador_no_ve_registrar_usuario(page: Page):
    iniciar_sesion(page, rol="evaluador")
    page.goto(f"{FRONTEND}/usuarios/nuevo")
    expect(page).to_have_url(f"{FRONTEND}/evaluaciones")
    expect(page.get_by_role("heading", name="Mis evaluaciones")).to_be_visible()
