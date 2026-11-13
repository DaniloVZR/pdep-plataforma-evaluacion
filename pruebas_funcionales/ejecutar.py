"""Ejecuta las pruebas funcionales del RTF4 v2 en orden y guarda los reportes.

Antes de correrlo, en otras dos terminales:
    flask --app app run          (raíz del repo)
    npm run dev                  (carpeta frontend/)

Luego, desde la raíz del repo:
    python pruebas_funcionales/ejecutar.py --ejecutor "Nombre de quien ejecuta"

Qué hace:
 1. Crea la base nueva (flask --app app init-db --demo) y carga datos_prueba.sql.
 2. Recorre CP-01 a CP-61 en el orden de la matriz (sección 5). Los casos de API los corre
    Newman con la colección de Postman y los de pantalla, pytest con Playwright. Cada tramo
    seguido de una misma herramienta se corre de una vez.
 3. Guarda en pruebas_funcionales/reportes/ el resultado de Newman (JSON) y de pytest (JUnit)
    de cada tramo, y el resumen por CP en reporte_pruebas.md.

Newman se busca en el PATH (npm install -g newman); si no está, se usa npx.
"""

import argparse
import json
import shutil
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CARPETA = Path(__file__).resolve().parent
REPO = CARPETA.parent
COLECCION = CARPETA / "postman" / "PDEP - Pruebas funcionales.postman_collection.json"
ENTORNO = CARPETA / "postman" / "PDEP local.postman_environment.json"
REPORTES = CARPETA / "reportes"
API = "http://127.0.0.1:5000"
FRONTEND = "http://localhost:5173"

HU = {**{cp: "HU-003" for cp in range(1, 18)},
      **{cp: "HU-005" for cp in range(18, 35)},
      **{cp: "HU-007" for cp in range(35, 56)},
      **{cp: "Todas" for cp in range(56, 62)}}
TAREA = {"HU-003": "PDEP-61", "HU-005": "PDEP-62", "HU-007": "PDEP-63"}

# Casos de API (sección 6) y el inicio de sesión que necesita cada uno en la colección.
LOGIN = {
    **{cp: "Login administrador (HU-003)" for cp in (3, 9, 10, 12, 13, 14)},
    16: "Login estudiante (HU-003)",
    **{cp: "Login estudiante (HU-005)" for cp in (19, 23, 24, 25, 26, 29, 32)},
    34: "Login evaluador (HU-005)",
    **{cp: "Login evaluador (HU-007)" for cp in (36, 37, 39, 40, 45, 49, 51, 52, 53)},
    55: "Login estudiante (HU-007)",
    59: None, 60: None, 61: None,
}


def pasos():
    """Orden de la matriz. La preparación va al inicio y las asignaciones de HU-006 van
    después de CP-31 y antes de CP-46, como dice la sección 4."""
    lista = [("preparacion", "Preparación")]
    for cp in range(1, 62):
        lista.append(("api" if cp in LOGIN else "pantalla", cp))
        if cp == 31:
            lista.append(("preparacion", "Preparación HU-007 - asignaciones"))
    tramos = []
    for tipo, valor in lista:
        if tramos and tramos[-1][0] == tipo and tipo != "preparacion":
            tramos[-1][1].append(valor)
        else:
            tramos.append((tipo, [valor]))
    return tramos


def comprobar_servidores() -> None:
    for nombre, url in (("Flask", f"{API}/api/login"), ("Frontend", FRONTEND)):
        try:
            urllib.request.urlopen(url, timeout=5)
        except urllib.error.HTTPError:
            pass                      # responde, aunque sea con error: está encendido
        except OSError:
            sys.exit(f"{nombre} no responde en {url}. Enciéndelo antes de ejecutar.")


def preparar_base() -> None:
    subprocess.run([sys.executable, "-m", "flask", "--app", "app", "init-db", "--demo"],
                   cwd=REPO, check=True)
    conexion = sqlite3.connect(REPO / "instance" / "pdep.sqlite3")
    conexion.executescript((CARPETA / "datos_prueba.sql").read_text(encoding="utf-8"))
    conexion.commit()
    conexion.close()


def comando_newman() -> list[str]:
    if shutil.which("newman"):
        return [shutil.which("newman")]
    if shutil.which("npx"):
        return [shutil.which("npx"), "--yes", "newman"]
    sys.exit("No encuentro Newman. Instálalo con: npm install -g newman")


def correr_newman(carpetas: list[str], salida: Path, entorno: Path) -> list[dict]:
    args = comando_newman() + ["run", str(COLECCION), "-e", str(entorno),
                               "--export-environment", str(entorno),
                               "-r", "json", "--reporter-json-export", str(salida)]
    for carpeta in carpetas:
        args += ["--folder", carpeta]
    subprocess.run(args, capture_output=True, check=False)
    datos = json.loads(salida.read_text(encoding="utf-8"))
    resultados = []
    for ejecucion in datos["run"]["executions"]:
        nombre = ejecucion["item"]["name"]
        afirmaciones = ejecucion.get("assertions", [])
        fallas = [f'{a["assertion"]}: {a["error"]["message"]}'
                  for a in afirmaciones if a.get("error")]
        if not afirmaciones:
            fallas = ["La petición no se pudo enviar."]
        respuesta = ejecucion.get("response") or {}
        resultados.append({"nombre": nombre, "fallas": fallas,
                           "estado_http": respuesta.get("code"),
                           "pruebas": [a["assertion"] for a in afirmaciones]})
    return resultados


def correr_pytest(cps: list[int], salida: Path, extra: list[str]) -> dict[int, dict]:
    filtro = " or ".join(f"test_cp{cp:02d}_" for cp in cps)
    subprocess.run([sys.executable, "-m", "pytest", ".", "-k", filtro, "-p", "no:cacheprovider",
                    "--junitxml", str(salida), "-q", *extra],
                   cwd=CARPETA / "playwright", check=False)
    resultados = {}
    for caso in ET.parse(salida).getroot().iter("testcase"):
        nombre = caso.get("name").split("[")[0]
        cp = int(nombre[len("test_cp"):len("test_cp") + 2])
        falla = caso.find("failure")
        if falla is None:
            falla = caso.find("error")
        resultados[cp] = {"nombre": nombre,
                          "fallas": [] if falla is None else [falla.get("message") or "Error"]}
    return resultados


def escribir_reporte(resultados: dict[int, dict], preparacion: list[dict], inicio: datetime,
                     fin: datetime, ejecutor: str, commit: str) -> Path:
    pasaron = sum(1 for r in resultados.values() if not r["fallas"])
    filas = []
    for cp in range(1, 62):
        r = resultados.get(cp, {"herramienta": "-", "nombre": "(no se ejecutó)",
                                "fallas": ["No se ejecutó."]})
        estado = "Pasó" if not r["fallas"] else "Falló"
        detalle = "; ".join(r["fallas"]).replace("|", "/").replace("\n", " ")[:300]
        filas.append(f"| CP-{cp:02d} | {HU[cp]} | {r['herramienta']} | `{r['nombre']}` | "
                     f"{estado} | {detalle} |")
    por_hu = []
    for hu in ("HU-003", "HU-005", "HU-007", "Todas"):
        casos = [cp for cp in range(1, 62) if HU[cp] == hu]
        bien = sum(1 for cp in casos if cp in resultados and not resultados[cp]["fallas"])
        tarea = f" ({TAREA[hu]})" if hu in TAREA else ""
        por_hu.append(f"| {hu}{tarea} | {len(casos)} | {bien} | {len(casos) - bien} |")
    prep_fallas = [p for p in preparacion if p["fallas"]]
    texto = f"""# Reporte de pruebas funcionales (RTF4 v2)

Plataforma de evaluación de proyectos institucionales: pruebas de caja negra de HU-003,
HU-005 y HU-007.

- **Fecha de ejecución:** {inicio:%d/%m/%Y}, de {inicio:%H:%M} a {fin:%H:%M} (hora de Colombia)
- **Ejecutado por:** {ejecutor}
- **Versión probada:** commit `{commit}` de la rama de pruebas
- **Base de datos:** nueva, con `flask --app app init-db --demo` y `pruebas_funcionales/datos_prueba.sql`
- **Herramientas:** Postman/Newman para la API ({sum(1 for r in resultados.values() if r['herramienta'] == 'Postman')} casos) y Playwright con pytest para las pantallas ({sum(1 for r in resultados.values() if r['herramienta'] == 'Playwright')} casos)
- **Orden:** el de la matriz de la sección 5, de CP-01 a CP-61
- **Resultado:** {pasaron} de 61 casos pasaron
- **Preparación** (ferias por fechas y asignaciones de HU-006): {"sin problemas" if not prep_fallas else "con fallas: " + ", ".join(p["nombre"] for p in prep_fallas)}

## Resumen por historia

| Historia | Casos | Pasaron | Fallaron |
|---|---|---|---|
{chr(10).join(por_hu)}

## Resultado de cada caso

| CP | HU | Herramienta | Prueba | Resultado | Detalle si falló |
|---|---|---|---|---|---|
{chr(10).join(filas)}

Los archivos de cada tramo están en esta misma carpeta: `newman/` (resultado JSON de
Newman) y `pytest/` (resultado JUnit de pytest).
"""
    destino = REPORTES / "reporte_pruebas.md"
    destino.write_text(texto, encoding="utf-8")
    (REPORTES / "resultados.json").write_text(json.dumps(
        {"fecha": inicio.isoformat(), "ejecutor": ejecutor, "commit": commit,
         "casos": {f"CP-{cp:02d}": {"hu": HU[cp], **resultados[cp]}
                   for cp in sorted(resultados)}},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def main() -> None:
    argumentos = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    argumentos.add_argument("--ejecutor", required=True, help="Quién ejecuta las pruebas.")
    argumentos.add_argument("--canal-navegador", default=None,
                            help="Navegador de Playwright, por ejemplo chrome o msedge. "
                                 "Sin este dato usa el Chromium de 'playwright install'.")
    opciones = argumentos.parse_args()
    extra = ["--browser-channel", opciones.canal_navegador] if opciones.canal_navegador else []

    comprobar_servidores()
    zona = ZoneInfo("America/Bogota")
    inicio = datetime.now(zona)
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO,
                            capture_output=True, text=True).stdout.strip() or "desconocido"
    shutil.rmtree(REPORTES, ignore_errors=True)
    (REPORTES / "newman").mkdir(parents=True)
    (REPORTES / "pytest").mkdir()
    entorno = REPORTES / "newman" / "entorno-final.postman_environment.json"
    shutil.copy(ENTORNO, entorno)

    preparar_base()
    resultados: dict[int, dict] = {}
    preparacion: list[dict] = []
    for numero, (tipo, valores) in enumerate(pasos(), start=1):
        if tipo == "pantalla":
            print(f"[{numero:02d}] Playwright: " + ", ".join(f"CP-{cp:02d}" for cp in valores))
            salida = REPORTES / "pytest" / f"{numero:02d}-CP-{valores[0]:02d}.xml"
            for cp, r in correr_pytest(valores, salida, extra).items():
                resultados[cp] = {"herramienta": "Playwright", **r}
            continue
        if tipo == "preparacion":
            print(f"[{numero:02d}] Postman: carpeta {valores[0]}")
            carpetas = valores
            salida = REPORTES / "newman" / f"{numero:02d}-preparacion.json"
        else:
            print(f"[{numero:02d}] Postman: " + ", ".join(f"CP-{cp:02d}" for cp in valores))
            carpetas = []
            for cp in valores:
                if LOGIN[cp] and LOGIN[cp] not in carpetas:
                    carpetas.append(LOGIN[cp])
                carpetas.append(f"CP-{cp:02d}")
            salida = REPORTES / "newman" / f"{numero:02d}-CP-{valores[0]:02d}.json"
        for r in correr_newman(carpetas, salida, entorno):
            if r["nombre"].startswith("CP-"):
                resultados[int(r["nombre"][3:])] = {"herramienta": "Postman", **r}
            else:
                preparacion.append(r)
    # El entorno final guarda los tokens de la corrida; no se deja en el reporte.
    entorno.unlink()

    destino = escribir_reporte(resultados, preparacion, inicio, datetime.now(zona),
                               opciones.ejecutor, commit)
    pasaron = sum(1 for r in resultados.values() if not r["fallas"])
    print(f"\n{pasaron} de 61 casos pasaron. Reporte: {destino.relative_to(REPO)}")
    sys.exit(0 if pasaron == 61 else 1)


if __name__ == "__main__":
    main()
