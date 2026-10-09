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

flask --app app init-db --demo   # crea instance/pdep.sqlite3 con datos de ejemplo
flask --app app run              # http://127.0.0.1:5000
```

Ejemplos con los datos de demostración:

```bash
curl -X POST http://127.0.0.1:5000/api/usuarios -H "Content-Type: application/json" \
  -d '{"nombres": "Ana", "correo": "ana@pascualbravo.edu.co", "rol": "ESTUDIANTE", "programa_id": 1, "asignatura_ids": [1]}'

curl -X POST http://127.0.0.1:5000/api/proyectos -H "Content-Type: application/json" \
  -d '{"equipo_id": 1, "feria_id": 1, "nombre": "Robot clasificador", "modalidad": "PIA", "asignatura_ids": [1, 2]}'

curl -X PUT http://127.0.0.1:5000/api/proyectos/1/evaluacion -H "Content-Type: application/json" \
  -d '{"evaluador_id": 1, "notas": {"1": 4.0, "2": 3.0, "3": 5.0}, "confirmar": true}'
```

## Pruebas y análisis estático

```bash
coverage run -m pytest      # 123 pruebas
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
- **Duplicados simultáneos (RNF-02):** además de la consulta previa, la base de
  datos tiene restricciones UNIQUE y cada escritura va en una transacción.
