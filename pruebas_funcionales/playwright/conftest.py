"""Ayudas comunes de las pruebas de pantalla del RTF4 v2 (sección 6, Playwright).

Antes de correrlas: base nueva (init-db --demo + datos_prueba.sql), Flask en
http://127.0.0.1:5000 y el frontend en http://localhost:5173 (npm run dev).
Los casos se ejecutan en el orden del RTF4, porque algunos usan lo que dejó otro.
"""

import os

import pytest
from playwright.sync_api import Page, expect

FRONTEND = os.environ.get("PDEP_FRONTEND", "http://localhost:5173")
API = os.environ.get("PDEP_API", "http://127.0.0.1:5000")

CUENTAS = {
    "administrador": ("admin@pascualbravo.edu.co", "admin123", "/admin"),
    "evaluador": ("evaluador@pascualbravo.edu.co", "evaluador123", "/evaluaciones"),
    "estudiante": ("estudiante@pascualbravo.edu.co", "estudiante123", "/proyectos/inscribir"),
}


@pytest.fixture
def browser_context_args(browser_context_args):
    """El navegador usa la hora de Colombia, igual que el backend."""
    return {**browser_context_args, "timezone_id": "America/Bogota", "locale": "es-CO"}


def iniciar_sesion(page: Page, rol: str) -> None:
    """Entra con la cuenta de prueba del rol y espera su pantalla de inicio."""
    correo, clave, inicio = CUENTAS[rol]
    page.goto(f"{FRONTEND}/ingresar")
    page.get_by_label("Correo institucional").fill(correo)
    page.get_by_label("Contraseña", exact=True).fill(clave)
    page.get_by_role("button", name="Ingresar").click()
    expect(page).to_have_url(f"{FRONTEND}{inicio}")


def elegir_opcion(page: Page, texto: str) -> None:
    """Pulsa una opción de un selector de botones (Rol, Modalidad), como lo hace el usuario."""
    opcion = page.locator(".selector-segmentado label").filter(has_text=texto)
    opcion.click()
    expect(opcion.get_by_role("radio")).to_be_checked()


def error_del_campo(page: Page, etiqueta: str):
    """Texto rojo que aparece debajo del campo con esa etiqueta."""
    return (page.locator(".campo, .criterio")
            .filter(has=page.locator("label", has_text=etiqueta))
            .locator(".campo-error"))


@pytest.fixture
def peticiones(page: Page) -> list[str]:
    """Peticiones a la API que hace la pantalla durante la prueba, como "POST /api/usuarios"."""
    enviadas: list[str] = []
    page.on("request", lambda r: enviadas.append(
        f"{r.method} {r.url.split('5173', 1)[-1].split('?')[0]}") if "/api/" in r.url else None)
    return enviadas


def consultar_api(page: Page, rol: str, ruta: str):
    """GET a la API con el token del rol, para revisar qué quedó guardado."""
    correo, clave, _ = CUENTAS[rol]
    token = page.request.post(f"{API}/api/login",
                              data={"correo": correo, "clave": clave}).json()["token"]
    respuesta = page.request.get(f"{API}{ruta}", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.ok, f"GET {ruta} respondió {respuesta.status}"
    return respuesta.json()


def id_feria(page: Page, nombre: str) -> int:
    """Id de una feria por su nombre (las ferias por fechas se crean el día de la prueba)."""
    return next(f["id"] for f in consultar_api(page, "administrador", "/api/ferias")
                if f["nombre"] == nombre)


def fecha_de_hoy_en_pantalla(page: Page) -> str:
    """La fecha de hoy con el mismo formato que usa la aplicación (por ejemplo 13 nov 2026)."""
    return page.evaluate("() => new Date().toLocaleDateString('es-CO', "
                         "{day: 'numeric', month: 'short', year: 'numeric'})")
