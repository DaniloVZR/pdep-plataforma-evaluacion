-- Datos de demostración para probar los endpoints a mano.
-- Las fechas de la feria 1 cubren todo 2026 para que la inscripción esté abierta.

INSERT INTO institucion (id, nombre, nit) VALUES
    (1, 'Institución Universitaria Pascual Bravo', '890980153');
INSERT INTO dominio_institucion (institucion_id, dominio) VALUES
    (1, 'pascualbravo.edu.co');

INSERT INTO programa (id, institucion_id, codigo, nombre) VALUES
    (1, 1, 'TDS', 'Tecnología en Desarrollo de Software');
INSERT INTO asignatura (id, programa_id, codigo, nombre, semestre) VALUES
    (1, 1, 'IS2', 'Ingeniería de Software II', 5),
    (2, 1, 'BD2', 'Bases de Datos II', 5),
    (3, 1, 'RD2', 'Redes de Datos II', 5);

INSERT INTO usuario (id, nombres, correo, rol, programa_id) VALUES
    (1, 'Docente Evaluador', 'evaluador@pascualbravo.edu.co', 'DOCENTE', 1),
    (2, 'Estudiante Demo', 'estudiante@pascualbravo.edu.co', 'ESTUDIANTE', 1);

INSERT INTO equipo (id, nombre) VALUES (1, 'Equipo Demo');
INSERT INTO equipo_integrante (equipo_id, usuario_id) VALUES (1, 2);

INSERT INTO feria (id, institucion_id, nombre, fecha_inicio, fecha_fin) VALUES
    (1, 1, 'Feria de Proyectos 2026-2', '2026-01-01', '2026-12-31');
INSERT INTO feria_asignatura (feria_id, asignatura_id) VALUES (1, 1), (1, 2);

INSERT INTO rubrica (id, feria_id, nota_minima, nota_maxima) VALUES (1, 1, 1.0, 5.0);
INSERT INTO criterio (id, rubrica_id, nombre, peso) VALUES
    (1, 1, 'Funcionalidad', 0.5),
    (2, 1, 'Calidad del código', 0.3),
    (3, 1, 'Presentación', 0.2);

INSERT INTO proyecto (id, equipo_id, feria_id, nombre, nombre_normalizado, modalidad,
                      fecha_inscripcion) VALUES
    (1, 1, 1, 'Proyecto Demo', 'proyecto demo', 'PA', '2026-10-01');
INSERT INTO proyecto_asignatura (proyecto_id, asignatura_id) VALUES (1, 1);

-- La asignación del evaluador (HU-006) crea la evaluación en estado PENDIENTE.
INSERT INTO evaluacion (id, proyecto_id, evaluador_id) VALUES (1, 1, 1);
