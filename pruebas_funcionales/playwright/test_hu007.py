"""HU-007 · Calificar proyecto con rúbrica y confirmar (pantalla /evaluaciones/{id}).
RTF4 v2, sección 5."""

from playwright.sync_api import Page, expect

from conftest import FRONTEND, consultar_api, error_del_campo, id_feria, iniciar_sesion

AVISO_CONFIRMAR = ("Al confirmar se publica el puntaje y ya no podrás cambiar las notas. "
                   "¿Continuar?")


def abrir_evaluacion(page: Page, proyecto_id: int) -> None:
    iniciar_sesion(page, rol="evaluador")
    page.goto(f"{FRONTEND}/evaluaciones/{proyecto_id}")


def abrir_desde_mis_evaluaciones(page: Page, proyecto: str) -> None:
    iniciar_sesion(page, rol="evaluador")
    fila = page.get_by_role("row").filter(
        has=page.get_by_role("cell", name=proyecto, exact=True))
    fila.get_by_role("link").click()
    expect(page.get_by_role("heading", name=proyecto)).to_be_visible()


def poner_notas(page: Page, funcionalidad: str, calidad: str, presentacion: str) -> None:
    page.get_by_label("Funcionalidad").fill(funcionalidad)
    page.get_by_label("Calidad del código").fill(calidad)
    page.get_by_label("Presentación").fill(presentacion)


def confirmar(page: Page, aceptar: bool) -> list[str]:
    """Pulsa Confirmar evaluación y responde la ventana; devuelve el texto que mostró."""
    mensajes: list[str] = []

    def responder(dialogo):
        mensajes.append(dialogo.message)
        if aceptar:
            dialogo.accept()
        else:
            dialogo.dismiss()

    page.once("dialog", responder)
    page.get_by_role("button", name="Confirmar evaluación").click()
    return mensajes


def estado_en_mis_evaluaciones(page: Page, proyecto: str):
    page.get_by_role("link", name="Mis evaluaciones").first.click()
    expect(page.get_by_role("heading", name="Mis evaluaciones")).to_be_visible()
    fila = page.get_by_role("row").filter(
        has=page.get_by_role("cell", name=proyecto, exact=True))
    return fila.locator(".insignia")


def test_cp35_nota_vacia_marca_el_criterio(page: Page, peticiones):
    abrir_evaluacion(page, 1)
    poner_notas(page, "4.0", "3.0", "")
    page.get_by_role("button", name="Guardar borrador").click()
    expect(page.get_by_label("Presentación")).to_have_attribute("aria-invalid", "true")
    expect(error_del_campo(page, "Presentación")).to_have_text("Falta la nota.")
    assert "PUT /api/proyectos/1/evaluacion" not in peticiones
    expect(estado_en_mis_evaluaciones(page, "Proyecto Demo")).to_have_text("Pendiente")


def test_cp38_nota_mayor_a_5_marca_el_criterio(page: Page, peticiones):
    abrir_evaluacion(page, 1)
    poner_notas(page, "5.01", "3.0", "5.0")
    page.get_by_role("button", name="Guardar borrador").click()
    expect(page.get_by_label("Funcionalidad")).to_have_attribute("aria-invalid", "true")
    expect(error_del_campo(page, "Funcionalidad")).to_have_text("Debe estar entre 1 y 5.")
    assert "PUT /api/proyectos/1/evaluacion" not in peticiones


def test_cp41_guardar_borrador_sin_puntaje(page: Page):
    abrir_evaluacion(page, 1)
    poner_notas(page, "4.0", "3.0", "5.0")
    page.get_by_role("button", name="Guardar borrador").click()
    expect(page.get_by_role("status")).to_have_text(
        "Borrador guardado. El puntaje se calcula y se publica cuando confirmes.")
    expect(page.locator(".resultado-puntaje")).to_have_count(0)
    expect(estado_en_mis_evaluaciones(page, "Proyecto Demo")).to_have_text("Borrador")


def test_cp42_cancelar_la_confirmacion_no_envia_nada(page: Page, peticiones):
    abrir_evaluacion(page, 1)
    expect(page.get_by_label("Funcionalidad")).to_have_value("4")
    expect(page.get_by_label("Calidad del código")).to_have_value("3")
    expect(page.get_by_label("Presentación")).to_have_value("5")
    assert confirmar(page, aceptar=False) == [AVISO_CONFIRMAR]
    assert "PUT /api/proyectos/1/evaluacion" not in peticiones
    expect(page.get_by_role("button", name="Confirmar evaluación")).to_be_visible()
    expect(page.get_by_label("Funcionalidad")).to_have_value("4")
    expect(page.locator(".resultado-puntaje")).to_have_count(0)


def test_cp43_confirmar_muestra_puntaje_3_90(page: Page):
    abrir_evaluacion(page, 1)
    assert confirmar(page, aceptar=True) == [AVISO_CONFIRMAR]
    expect(page.get_by_text("Evaluación confirmada", exact=True)).to_be_visible()
    expect(page.locator(".resultado-puntaje")).to_have_text("3.90 / 5")
    expect(page.get_by_text("Confirmada el")).to_be_visible()


def test_cp44_evaluacion_confirmada_queda_solo_lectura(page: Page):
    abrir_desde_mis_evaluaciones(page, "Proyecto Demo")
    expect(page.get_by_text("Evaluación confirmada", exact=True)).to_be_visible()
    expect(page.locator(".resultado-puntaje")).to_have_text("3.90 / 5")
    expect(page.get_by_role("spinbutton")).to_have_count(0)
    expect(page.get_by_role("button", name="Guardar borrador")).to_have_count(0)
    expect(page.get_by_role("button", name="Confirmar evaluación")).to_have_count(0)


def test_cp46_confirmar_desde_pendiente_muestra_5_00(page: Page):
    abrir_desde_mis_evaluaciones(page, "Huerta inteligente")
    poner_notas(page, "5.0", "5.0", "5.0")
    confirmar(page, aceptar=True)
    expect(page.get_by_text("Evaluación confirmada", exact=True)).to_be_visible()
    expect(page.locator(".resultado-puntaje")).to_have_text("5.00 / 5")


def test_cp47_limites_de_la_escala_muestran_2_60(page: Page):
    abrir_desde_mis_evaluaciones(page, "Reciclaje escolar")
    poner_notas(page, "1.0", "5.0", "3.0")
    confirmar(page, aceptar=True)
    expect(page.get_by_text("Evaluación confirmada", exact=True)).to_be_visible()
    expect(page.locator(".resultado-puntaje")).to_have_text("2.60 / 5")


def test_cp48_proyecto_no_asignado_muestra_recuadro_rojo(page: Page):
    proyectos = consultar_api(page, "administrador",
                              f"/api/proyectos?feria_id={id_feria(page, 'Feria termina hoy')}")
    biblioteca = next(p["id"] for p in proyectos if p["nombre"] == "Biblioteca digital")
    abrir_evaluacion(page, biblioteca)
    expect(page.get_by_role("alert")).to_have_text(
        "No tienes asignado este proyecto, así que no puedes calificarlo.")
    expect(page.get_by_role("spinbutton")).to_have_count(0)


def test_cp50_feria_sin_rubrica_no_muestra_el_formulario(page: Page):
    abrir_evaluacion(page, 90)
    alerta = page.get_by_role("alert")
    expect(alerta).to_contain_text("La feria no tiene una rúbrica asociada.")
    expect(alerta.get_by_role("button", name="Reintentar")).to_be_visible()
    expect(page.get_by_role("spinbutton")).to_have_count(0)


def test_cp54_estudiante_no_ve_calificar_proyecto(page: Page):
    iniciar_sesion(page, rol="estudiante")
    page.goto(f"{FRONTEND}/evaluaciones/1")
    expect(page).to_have_url(f"{FRONTEND}/proyectos/inscribir")
    expect(page.get_by_role("heading", name="Inscribir proyecto")).to_be_visible()
