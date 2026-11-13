"""Todas las HU · Abrir las pantallas sin iniciar sesión (CP-56 a CP-58). RTF4 v2, sección 5."""

from playwright.sync_api import Page, expect

from conftest import FRONTEND


def test_cp56_sin_sesion_registrar_usuario_lleva_a_ingresar(page: Page):
    page.goto(f"{FRONTEND}/usuarios/nuevo")
    expect(page).to_have_url(f"{FRONTEND}/ingresar")
    expect(page.get_by_role("heading", name="Iniciar sesión")).to_be_visible()


def test_cp57_sin_sesion_inscribir_proyecto_lleva_a_ingresar(page: Page):
    page.goto(f"{FRONTEND}/proyectos/inscribir")
    expect(page).to_have_url(f"{FRONTEND}/ingresar")


def test_cp58_sin_sesion_calificar_proyecto_lleva_a_ingresar(page: Page):
    page.goto(f"{FRONTEND}/evaluaciones/1")
    expect(page).to_have_url(f"{FRONTEND}/ingresar")
