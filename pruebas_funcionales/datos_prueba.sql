-- Datos de prueba de las pruebas funcionales (RTF4 v2, sección 4, fila
-- "Rúbricas que no cumplen las reglas"). Se usan en CP-50 a CP-53 (HU-007, RN005).
--
-- Estas ferias no se pueden crear desde la pantalla Ferias ni con POST /api/ferias,
-- porque HU-004 exige rúbrica con criterios y pesos que sumen 100 %. Por eso van por SQL.
--
-- Cómo se cargan (desde la raíz del repo, justo después de crear la base):
--   flask --app app init-db --demo
--   python -c "import sqlite3; c=sqlite3.connect('instance/pdep.sqlite3'); c.executescript(open('pruebas_funcionales/datos_prueba.sql', encoding='utf-8').read()); c.commit()"
--
-- Usa la feria, el equipo y el evaluador de la base de demostración (Equipo Demo, id 1;
-- Docente Evaluador, id 1). Las fechas cubren todo 2026, igual que la feria 1.

-- Feria sin rúbrica (id 90): no tiene fila en rubrica.
INSERT INTO feria (id, institucion_id, nombre, fecha_inicio, fecha_fin) VALUES
    (90, 1, 'Feria sin rúbrica', '2026-01-01', '2026-12-31');

-- Feria pesos 80 (id 91): Funcionalidad 50 % + Presentación 30 % = 80 %.
INSERT INTO feria (id, institucion_id, nombre, fecha_inicio, fecha_fin) VALUES
    (91, 1, 'Feria pesos 80', '2026-01-01', '2026-12-31');
INSERT INTO rubrica (id, feria_id, nota_minima, nota_maxima) VALUES (91, 91, 1.0, 5.0);
INSERT INTO criterio (id, rubrica_id, nombre, peso) VALUES
    (910, 91, 'Funcionalidad', 0.5),
    (911, 91, 'Presentación', 0.3);

-- Feria sin criterios (id 92): tiene rúbrica, pero ningún criterio.
INSERT INTO feria (id, institucion_id, nombre, fecha_inicio, fecha_fin) VALUES
    (92, 1, 'Feria sin criterios', '2026-01-01', '2026-12-31');
INSERT INTO rubrica (id, feria_id, nota_minima, nota_maxima) VALUES (92, 92, 1.0, 5.0);

INSERT INTO feria_asignatura (feria_id, asignatura_id) VALUES (90, 1), (91, 1), (92, 1);

-- El proyecto "Robot seguidor" en cada una (ids 90, 91 y 92), inscrito por el Equipo Demo.
INSERT INTO proyecto (id, equipo_id, feria_id, nombre, nombre_normalizado, modalidad,
                      fecha_inscripcion) VALUES
    (90, 1, 90, 'Robot seguidor', 'robot seguidor', 'PA', '2026-10-01'),
    (91, 1, 91, 'Robot seguidor', 'robot seguidor', 'PA', '2026-10-01'),
    (92, 1, 92, 'Robot seguidor', 'robot seguidor', 'PA', '2026-10-01');
INSERT INTO proyecto_asignatura (proyecto_id, asignatura_id) VALUES (90, 1), (91, 1), (92, 1);

-- Cada uno con su evaluación Pendiente para Docente Evaluador, como si HU-006 lo hubiera
-- asignado. Sin esta fila la pantalla diría "No tienes asignado este proyecto" en vez de
-- mostrar el problema de la rúbrica (CP-50).
INSERT INTO evaluacion (id, proyecto_id, evaluador_id) VALUES
    (90, 90, 1),
    (91, 91, 1),
    (92, 92, 1);
