"""HU-005 · Inscribir proyecto en una feria (pantalla /proyectos/inscribir). RTF4 v2, sección 5."""

from playwright.sync_api import Page, expect

from conftest import (FRONTEND, consultar_api, elegir_opcion, error_del_campo,
                      fecha_de_hoy_en_pantalla, id_feria, iniciar_sesion)


def abrir_inscripcion(page: Page) -> None:
    iniciar_sesion(page, rol="estudiante")
    expect(page.get_by_role("heading", name="Inscribir proyecto")).to_be_visible()
    page.get_by_label("Equipo", exact=True).select_option(label="Equipo Demo")


def elegir_feria(page: Page, feria: str) -> None:
    page.get_by_label("Feria", exact=True).select_option(label=feria)


def llenar(page: Page, feria: str | None, nombre: str, modalidad: str = "PA",
           asignaturas: tuple[str, ...] = ("Ingeniería de Software II",)) -> None:
    if feria:
        elegir_feria(page, feria)
    page.get_by_label("Nombre del proyecto").fill(nombre)
    elegir_opcion(page, "Proyecto de Aula (PA)" if modalidad == "PA"
                  else "Proyecto Integrador (PIA)")
    if feria:
        for asignatura in asignaturas:
            page.get_by_label(asignatura).check()


def inscribir(page: Page) -> None:
    page.get_by_role("button", name="Inscribir proyecto").click()


def etiqueta_de_plazo(page: Page):
    return (page.locator(".campo").filter(has=page.get_by_label("Feria", exact=True))
            .locator(".insignia"))


def proyectos_en(page: Page, feria: str, nombre: str) -> int:
    proyectos = consultar_api(page, "administrador",
                              f"/api/proyectos?feria_id={id_feria(page, feria)}")
    return sum(1 for p in proyectos if p["nombre"] == nombre)


def test_cp18_inscribe_proyecto_en_feria_abierta(page: Page):
    abrir_inscripcion(page)
    elegir_feria(page, "Feria abierta")
    expect(etiqueta_de_plazo(page)).to_have_text("Inscripción abierta")
    llenar(page, "Feria abierta", "Huerta inteligente")
    inscribir(page)
    aviso = page.get_by_role("status")
    expect(aviso).to_contain_text(
        f"El proyecto Huerta inteligente quedó inscrito el {fecha_de_hoy_en_pantalla(page)}")
    expect(aviso.get_by_role("link", name="Ver proyectos inscritos")).to_be_visible()


def test_cp20_nombre_vacio_marca_el_campo(page: Page, peticiones):
    abrir_inscripcion(page)
    llenar(page, "Feria abierta", "")
    inscribir(page)
    expect(page.get_by_label("Nombre del proyecto")).to_have_attribute("aria-invalid", "true")
    expect(error_del_campo(page, "Nombre del proyecto")).to_have_text(
        "Escribe el nombre del proyecto.")
    assert "POST /api/proyectos" not in peticiones


def test_cp21_sin_feria_marca_feria_y_asignaturas(page: Page, peticiones):
    abrir_inscripcion(page)
    llenar(page, None, "Reciclaje escolar")
    inscribir(page)
    expect(page.get_by_label("Feria", exact=True)).to_have_attribute("aria-invalid", "true")
    expect(error_del_campo(page, "Feria")).to_have_text("Elige la feria.")
    expect(page.get_by_text(
        "Elige primero la feria para ver sus asignaturas participantes.")).to_be_visible()
    expect(page.get_by_text("Elige al menos una asignatura.")).to_be_visible()
    assert "POST /api/proyectos" not in peticiones


def test_cp22_pia_con_una_asignatura_no_se_envia(page: Page, peticiones):
    abrir_inscripcion(page)
    llenar(page, "Feria abierta", "App de tutorías", modalidad="PIA")
    inscribir(page)
    expect(page.get_by_text(
        "Un Proyecto Integrador (PIA) requiere dos o más asignaturas.")).to_be_visible()
    assert "POST /api/proyectos" not in peticiones


def test_cp27_feria_futura_aun_no_abre(page: Page):
    abrir_inscripcion(page)
    elegir_feria(page, "Feria futura")
    expect(etiqueta_de_plazo(page)).to_have_text("Aún no abre")
    llenar(page, "Feria futura", "Reciclaje escolar")
    inscribir(page)
    expect(page.get_by_role("alert")).to_have_text(
        "La inscripción a la feria aún no está abierta.")
    assert proyectos_en(page, "Feria futura", "Reciclaje escolar") == 0


def test_cp28_feria_que_inicia_hoy_acepta_la_inscripcion(page: Page):
    abrir_inscripcion(page)
    elegir_feria(page, "Feria inicia hoy")
    expect(etiqueta_de_plazo(page)).to_have_text("Inscripción abierta")
    llenar(page, "Feria inicia hoy", "Reciclaje escolar")
    inscribir(page)
    expect(page.get_by_role("status")).to_contain_text(
        f"El proyecto Reciclaje escolar quedó inscrito el {fecha_de_hoy_en_pantalla(page)}")


def test_cp30_feria_vencida_plazo_vencido(page: Page):
    abrir_inscripcion(page)
    elegir_feria(page, "Feria vencida")
    expect(etiqueta_de_plazo(page)).to_have_text("Plazo vencido")
    llenar(page, "Feria vencida", "Reciclaje escolar")
    inscribir(page)
    expect(page.get_by_role("alert")).to_have_text(
        "El plazo de inscripción de la feria ya venció.")
    assert proyectos_en(page, "Feria vencida", "Reciclaje escolar") == 0


def test_cp31_proyecto_repetido_en_la_misma_feria(page: Page):
    abrir_inscripcion(page)
    llenar(page, "Feria abierta", "Huerta inteligente")
    inscribir(page)
    expect(page.get_by_role("alert")).to_have_text(
        "El equipo ya inscribió un proyecto con ese nombre en la feria.")
    assert proyectos_en(page, "Feria abierta", "Huerta inteligente") == 1


def test_cp33_evaluador_no_ve_inscribir_proyecto(page: Page):
    iniciar_sesion(page, rol="evaluador")
    page.goto(f"{FRONTEND}/proyectos/inscribir")
    expect(page).to_have_url(f"{FRONTEND}/evaluaciones")
    expect(page.get_by_role("heading", name="Mis evaluaciones")).to_be_visible()
