# PDEP · Plataforma de evaluación de proyectos institucionales

Prototipo del backend de la plataforma para ferias de proyectos de la Institución
Universitaria Pascual Bravo (Ingeniería de Software II, 2026-2).

Este incremento implementa las tres historias del Sprint 3 y sus pruebas
estructurales (caja blanca), según el diseño del documento RTF3:

| Historia | Jira | Endpoint | Servicio |
|---|---|---|---|
| HU-003 Registrar estudiantes y docentes | PDEP-7 | `POST /api/usuarios` | `RegistroUsuarioServicio.registrar` |
| HU-005 Inscribir un proyecto en una feria | PDEP-9 | `POST /api/proyectos` | `InscripcionServicio.inscribir` |
| HU-007 Calificar con rúbrica digital | PDEP-11 | `PUT /api/proyectos/<id>/evaluacion` | `CalificacionServicio.calificar` |

Sprint 6 agrega:

| Historia | Jira | Endpoints | Servicio |
|---|---|---|---|
| HU-001 Registrar institución, facultades, departamentos y programas | PDEP-5 | `POST /api/instituciones`, `POST /api/facultades`, `POST /api/departamentos`, `POST /api/programas` | `EstructuraAcademicaServicio` |
| HU-006 Asignar evaluadores a los proyectos | PDEP-10 | `POST /api/proyectos/<id>/evaluadores` | `AsignacionServicio.asignar` |

También se agregan (cada historia completa: backend, pruebas y pantalla):

| Historia | Jira | Endpoints | Servicio | Pantalla |
|---|---|---|---|---|
| HU-002 Registrar asignaturas y asociarlas a un programa | PDEP-6 | `POST /api/asignaturas`, `GET /api/asignaturas?programa_id=` | `RegistroAsignaturaServicio.registrar` | `/estructura/asignaturas` (administrador) |
| HU-009 Consultar calificación y retroalimentación | PDEP-13 | `GET /api/resultados?estudiante_id=` | `ConsultaResultadosServicio.consultar` | `/resultados` (estudiante) |
| HU-008 Cálculo automático del puntaje final | PDEP-12 | `PUT /api/proyectos/<id>/evaluacion` rechaza `puntaje_final`/`puntaje` (400) y triggers en `schema.sql` | `Rubrica.calcular_puntaje`, `rechazar_puntaje_manual` | `/evaluaciones/<id>` (solo lectura tras confirmar) |
| HU-010 Consolidar y generar reportes de resultados | PDEP-14 | `GET /api/reportes?agrupar_por=&feria_id=&asignatura_id=&programa_id=`, `GET /api/reportes/excel` (mismos parámetros) | `ReporteServicio.generar`, `generar_excel` | `/reportes` (administrador) |

Autores: Angelo Alexander Arango Graciano y Joimar Danilo Urrego David.

## Arquitectura

Cada solicitud recorre cuatro capas. Solo los repositorios conocen SQLite, por eso
las reglas de negocio se prueban sin base de datos.

```
controladores/   Recibe el JSON (Flask) y devuelve la respuesta HTTP.
servicios/       Coordina el caso de uso: valida, consulta y guarda.
validadores/     Funciones puras con las reglas de negocio (lanzan excepciones).
dominio/         Entidades (dataclasses) y excepciones con su código HTTP.
repositorios/    Contratos (Protocol) e implementación en SQLite con transacciones.
```

Las excepciones del dominio llegan al manejador `manejar_error_dominio` de
`create_app`, que responde `{"codigo": ..., "mensaje": ...}` con el código HTTP de
la excepción (400, 403, 404, 409, 422 o 500).

## Cómo ejecutarlo

Requiere Python 3.11 o superior.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt

flask --app app init-db --demo     # crea instance/pdep.sqlite3 con los datos mínimos
flask --app app init-db --ejemplo  # o: datos mínimos + datos de ejemplo para probar a mano
flask --app app run                # http://127.0.0.1:5000
```

`init-db` borra y vuelve a crear todas las tablas: lo registrado desde la app se pierde.
La base (`instance/`) no se sube al repositorio; cada uno tiene la suya.

- `--demo` carga `app/datos_demo.sql`: lo mínimo (una feria, un proyecto PENDIENTE y una
  cuenta por rol). Las pruebas automáticas usan este archivo, así que no conviene cambiarlo.
- `--ejemplo` carga además `app/datos_ejemplo.sql`, compartido por el equipo: 2 ferias con
  rúbricas distintas, 3 programas, 3 docentes más, 10 estudiantes, 6 equipos y 10 proyectos
  con evaluaciones confirmadas de todos los niveles, una en borrador, una sin empezar y un
  proyecto sin evaluador. Para ver con más datos las pantallas (sobre todo Reportes), se
  agregan aquí; `tests/integracion/test_datos_ejemplo.py` revisa que los puntajes coincidan
  con la rúbrica y que cada proyecto respete su feria y su modalidad.

### Cuentas de prueba (RNF-03)

`init-db --demo` crea una cuenta por rol para entrar a la aplicación. Las claves van en
texto plano porque es un prototipo académico; no use contraseñas reales.

| Rol | Correo | Clave |
|---|---|---|
| Administrador | `admin@pascualbravo.edu.co` | `admin123` |
| Evaluador (docente 1) | `evaluador@pascualbravo.edu.co` | `evaluador123` |
| Estudiante (usuario 2, Equipo Demo) | `estudiante@pascualbravo.edu.co` | `estudiante123` |
| Evaluadora (docente 3, solo con `--ejemplo`) | `carolina.restrepo@pascualbravo.edu.co` | `evaluador123` |
| Estudiante (usuario 6, solo con `--ejemplo`) | `laura.gomez@pascualbravo.edu.co` | `estudiante123` |

`POST /api/login` con `{"correo", "clave"}` responde 200 con `{"usuario_id", "nombre", "rol", "token"}`,
400 si falta un dato y 401 si el correo o la clave no coinciden. Las cuentas están en la tabla
`cuenta`, separada de `usuario`, así que el registro de HU-003 no cambia.

### Control de roles en la API (PDEP-47)

Todos los endpoints, menos `/api/login`, piden el token en el encabezado
`Authorization: Bearer <token>` (el frontend lo envía solo). El token está firmado con
`SECRET_KEY` y vence a las 8 horas; en un servidor real se define la variable de entorno
`PDEP_SECRET_KEY`.

| Endpoint | Rol que puede usarlo |
|---|---|
| `POST /api/usuarios`, `/instituciones`, `/facultades`, `/departamentos`, `/programas`, `/asignaturas`, `/ferias`, `/proyectos/<id>/evaluadores` | Administrador |
| `POST /api/proyectos` | Estudiante |
| `PUT /api/proyectos/<id>/evaluacion` | Evaluador, solo con su propio `evaluador_id` |
| `GET /api/resultados?estudiante_id=` | Estudiante, solo con su propio id |
| `GET /api/evaluaciones?evaluador_id=` | Evaluador, solo con su propio id |
| `GET /api/reportes`, `GET /api/reportes/excel` | Administrador |
| Los demás `GET` (listas) | Cualquier sesión |

El administrador puede usar todos, porque con "Ver como" revisa la plataforma desde los
otros roles. Sin token o con un token inválido la respuesta es 401 (`sesion_requerida`);
con otro rol, 403 (`sin_permiso`).

Ejemplos con los datos de demostración (primero se inicia sesión y se guarda el token):

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:5000/api/login -H "Content-Type: application/json" \
  -d '{"correo": "admin@pascualbravo.edu.co", "clave": "admin123"}' | python -c "import sys, json; print(json.load(sys.stdin)['token'])")

curl -X POST http://127.0.0.1:5000/api/usuarios -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"nombres": "Ana", "correo": "ana@pascualbravo.edu.co", "rol": "ESTUDIANTE", "programa_id": 1, "asignatura_ids": [1]}'

curl -X POST http://127.0.0.1:5000/api/proyectos -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"equipo_id": 1, "feria_id": 1, "nombre": "Robot clasificador", "modalidad": "PIA", "asignatura_ids": [1, 2]}'

curl -X PUT http://127.0.0.1:5000/api/proyectos/1/evaluacion -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"evaluador_id": 1, "notas": {"1": 4.0, "2": 3.0, "3": 5.0}, "confirmar": true}'

curl -X POST http://127.0.0.1:5000/api/facultades -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"institucion_id": 1, "nombre": "Facultad de Producción y Diseño"}'

curl -X POST http://127.0.0.1:5000/api/programas -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"institucion_id": 1, "codigo": "ISW", "nombre": "Ingeniería de Software", "facultad_id": 1}'

curl -X POST http://127.0.0.1:5000/api/ferias -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"institucion_id": 1, "nombre": "Feria 2027-1", "fecha_inicio": "2027-03-01", "fecha_fin": "2027-03-15", "asignatura_ids": [1, 2], "criterios": [{"nombre": "Funcionalidad", "peso": 0.6}, {"nombre": "Presentación", "peso": 0.4}]}'

curl -X POST http://127.0.0.1:5000/api/proyectos/1/evaluadores -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"evaluador_ids": [1]}'   # 409: el docente 1 ya evalúa el proyecto 1 (REQ-12)
```

## Endpoints de consulta para el frontend (PDEP-35)

Solo lectura. No pasan por los servicios de las historias, así que el diseño de
pruebas del RTF3 no cambia. Los errores siguen el formato `{"codigo", "mensaje"}`.

| Endpoint | Devuelve | Uso en el frontend |
|---|---|---|
| `GET /api/instituciones` | Instituciones con contacto y dominios | Estructura académica (HU-001) |
| `GET /api/facultades?institucion_id=1` | Facultades; el filtro es opcional | Estructura académica (HU-001) |
| `GET /api/departamentos?institucion_id=1` | Departamentos; el filtro es opcional | Estructura académica (HU-001) |
| `GET /api/asignaturas?programa_id=1` | Asignaturas con su programa, ordenadas por semestre; el filtro es opcional (404 si el programa no existe) | Pantalla de asignaturas (HU-002) |
| `GET /api/programas` | Programas con su facultad o departamento y sus asignaturas | Registro de usuarios (HU-003) y estructura (HU-001) |
| `GET /api/usuarios?rol=DOCENTE` | Usuarios; `rol` es opcional | Elegir el evaluador (HU-007) |
| `GET /api/equipos` | Equipos con sus integrantes | Formulario de inscripción (HU-005) |
| `GET /api/ferias` | Ferias con su institución, fechas y asignaturas participantes | Inscripción (HU-005) y ferias (HU-004) |
| `GET /api/ferias/<id>/rubrica` | Escala y criterios con su peso (404 si no existe la feria, 422 si no tiene rúbrica) | Pantalla de calificación (HU-007) |
| `GET /api/proyectos?feria_id=1` | Proyectos inscritos con sus evaluadores; `feria_id` es opcional | Listado de proyectos y asignación (HU-006) |
| `GET /api/evaluadores/carga` | Cada docente con sus proyectos asignados, pendientes, borradores y confirmados | Carga por evaluador (HU-006) |
| `GET /api/evaluaciones?evaluador_id=1` | Evaluaciones asignadas; el puntaje solo aparece si está CONFIRMADA (400 sin `evaluador_id`) | "Mis proyectos por calificar" (HU-007) |

### Conectar el frontend (Vite) con la API

Flask corre en el puerto 5000 y Vite en el 5173. Para que las rutas `/api/...` del
frontend lleguen a Flask sin configurar CORS, se agrega un proxy en
`frontend/vite.config.ts`:

```ts
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:5000' } },
})
```

Con eso basta tener las dos terminales abiertas: `flask --app app run` y `npm run dev`.

## Pruebas y análisis estático

```bash
coverage run -m pytest      # 310 pruebas
coverage report             # cobertura de líneas y de ramas (branch = true)
coverage html               # reporte navegable en htmlcov/index.html
pylint app tests            # análisis estático
```

- `tests/unitarias/`: un caso por cada camino básico de los servicios (nombres
  `test_c1_...` a `test_c12_...`, con la secuencia de nodos en el docstring) y
  pruebas parametrizadas de los valores límite de cada condición. Los
  repositorios se reemplazan por `Mock(spec=Contrato)` y el reloj por uno con
  fecha fija.
- `tests/integracion/`: repositorios contra una base SQLite temporal
  (restricciones UNIQUE, transacciones) y endpoints con el cliente de pruebas de Flask.

GitHub Actions ejecuta las pruebas, la cobertura y Pylint en cada `push` a `main`.

## Decisiones de diseño

- **Correo institucional (RN001):** se normaliza a minúsculas y el dominio se
  compara de forma exacta con los dominios registrados.
- **Plazo de inscripción (RN003):** se compara por fecha (`date`) en la zona horaria
  de Bogotá; el primer y el último día cuentan como válidos.
- **Mismo proyecto (RN002):** mismo equipo y mismo nombre normalizado en la misma feria.
- **Modalidad (RN009):** PA en una asignatura; PIA en dos o más.
- **Rúbrica (RN005, RN006):** pesos positivos que suman 1 con tolerancia de 1e-6;
  escala por defecto de 1.0 a 5.0; puntaje = Σ (nota × peso), redondeado a 2 decimales.
- **Confirmación (RN007):** el puntaje solo se publica al confirmar; una evaluación
  confirmada no se puede modificar.
- **Puntaje no modificable (HU-008, REQ-16):** el evaluador envía notas, nunca el
  puntaje; si la solicitud trae `puntaje_final` o `puntaje`, la API responde 400
  (`puntaje_no_editable`). Como segunda barrera, cuatro triggers de `schema.sql` impiden
  cambiar o borrar una evaluación CONFIRMADA y sus notas, aunque sea con SQL directo.
  Por eso `guardar_calificacion` reemplaza las notas antes de cambiar el estado.
- **Estructura académica (HU-001):** la institución exige nombre y NIT; la facultad
  y el departamento exigen nombre y no se repiten dentro de la institución (sin
  distinguir mayúsculas). El programa debe ir en una facultad o un departamento de
  su misma institución; las columnas aceptan NULL para no romper el programa existente.
- **Asignación de evaluadores (HU-006):** solo docentes; un evaluador no se asigna
  dos veces al mismo proyecto (REQ-12). La solicitud es todo o nada: si un evaluador
  falla, no se asigna ninguno. Cada asignación crea la evaluación PENDIENTE que usa HU-007.
- **Asignaturas (HU-002):** código, nombre, semestre (entero mayor que 0) y programa
  obligatorios; 404 si el programa no existe y 409 si el código ya está registrado (se
  guarda en mayúsculas). Usa la tabla `asignatura` que ya existía.
- **Retroalimentación y resultados (HU-009):** HU-007 acepta un campo opcional
  `retroalimentacion` (texto) que se guarda con la evaluación. `GET /api/resultados`
  devuelve los proyectos de los equipos del estudiante con cada evaluación; el puntaje y
  la retroalimentación solo salen si la evaluación está CONFIRMADA (RN007). Se muestran el
  evaluador y la fecha de confirmación (RNF-06). Solo un estudiante puede consultarlo (422).
- **Reportes de resultados (HU-010):** `GET /api/reportes` consolida los puntajes (REQ-18)
  y los agrupa por feria, asignatura o programa (`agrupar_por`, por defecto feria); también
  filtra por `feria_id`, `asignatura_id` y `programa_id` (REQ-19). Un proyecto entra al
  reporte solo si **todas** sus evaluaciones están CONFIRMADAS, y su puntaje es el promedio
  de sus evaluadores; los demás se cuentan como pendientes. Un PIA aparece en cada una de
  sus asignaturas. 400 si un filtro está mal escrito, 404 si lo filtrado no existe. La
  consulta usa siempre cinco sentencias SQL, sin importar cuántos proyectos haya; una prueba
  verifica 500 proyectos en menos de 5 segundos (RNF-01). Además trae:
  - **Distribución de notas** por nivel (Excelente ≥ 4.5, Bueno ≥ 4.0, Aceptable ≥ 3.0,
    Insuficiente < 3.0) con aprobados y reprobados, en total y por grupo.
  - **Promedio por criterio** de la rúbrica, por proyecto y por grupo.
  - **Avance de la evaluación**: evaluaciones confirmadas, en borrador y sin empezar, y los
    proyectos pendientes con el evaluador que falta.
  - **Detalle de cada proyecto**: integrantes, asignaturas y retroalimentación.
  - `GET /api/reportes/excel` descarga lo mismo en un `.xlsx` (openpyxl) con las hojas
    Resumen, Resultados, Por criterio, Retroalimentación y Pendientes.
- **Duplicados simultáneos (RNF-02):** además de la consulta previa, la base de
  datos tiene restricciones UNIQUE y cada escritura va en una transacción.
