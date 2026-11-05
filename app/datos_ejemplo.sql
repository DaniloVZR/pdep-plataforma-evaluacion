-- Datos de ejemplo para la demostración y las pruebas manuales.
-- Se cargan ENCIMA de datos_demo.sql con: flask --app app init-db --ejemplo
-- Las pruebas automáticas no los usan, así que se pueden ampliar sin romperlas;
-- tests/integracion/test_datos_ejemplo.py solo revisa que sean consistentes.
--
-- Cada puntaje_final es el que calcula HU-007 con la rúbrica de su feria:
-- Σ (nota del criterio × peso), redondeado a dos decimales.

-- ───────── Estructura académica (HU-001, HU-002) ─────────
INSERT INTO programa (id, institucion_id, facultad_id, codigo, nombre) VALUES
    (2, 1, 1, 'IEL', 'Ingeniería Eléctrica'),
    (3, 1, 1, 'ISW', 'Ingeniería de Software');

INSERT INTO asignatura (id, programa_id, codigo, nombre, semestre) VALUES
    (4, 2, 'CIR', 'Circuitos Eléctricos', 3),
    (5, 2, 'MAQ', 'Máquinas Eléctricas', 6),
    (6, 3, 'ARQ', 'Arquitectura de Software', 7),
    (7, 3, 'GPS', 'Gestión de Proyectos de Software', 8);

-- ───────── Docentes y estudiantes (HU-003) ─────────
INSERT INTO usuario (id, nombres, correo, rol, programa_id) VALUES
    (3, 'Carolina Restrepo', 'carolina.restrepo@pascualbravo.edu.co', 'DOCENTE', 1),
    (4, 'Andrés Mejía', 'andres.mejia@pascualbravo.edu.co', 'DOCENTE', 2),
    (5, 'Luisa Fernanda Ortiz', 'luisa.ortiz@pascualbravo.edu.co', 'DOCENTE', 3),
    (6, 'Laura Gómez', 'laura.gomez@pascualbravo.edu.co', 'ESTUDIANTE', 1),
    (7, 'Santiago Ríos', 'santiago.rios@pascualbravo.edu.co', 'ESTUDIANTE', 1),
    (8, 'Valentina Cardona', 'valentina.cardona@pascualbravo.edu.co', 'ESTUDIANTE', 1),
    (9, 'Juan Pablo Henao', 'juan.henao@pascualbravo.edu.co', 'ESTUDIANTE', 1),
    (10, 'Daniela Zapata', 'daniela.zapata@pascualbravo.edu.co', 'ESTUDIANTE', 2),
    (11, 'Mateo Arango', 'mateo.arango@pascualbravo.edu.co', 'ESTUDIANTE', 2),
    (12, 'Sara Londoño', 'sara.londono@pascualbravo.edu.co', 'ESTUDIANTE', 3),
    (13, 'Esteban Vélez', 'esteban.velez@pascualbravo.edu.co', 'ESTUDIANTE', 3),
    (14, 'Camila Ospina', 'camila.ospina@pascualbravo.edu.co', 'ESTUDIANTE', 3),
    (15, 'Tomás Cárdenas', 'tomas.cardenas@pascualbravo.edu.co', 'ESTUDIANTE', 1);

INSERT INTO usuario_asignatura (usuario_id, asignatura_id) VALUES
    (3, 1), (3, 2), (4, 4), (4, 5), (5, 6), (5, 7),
    (6, 1), (6, 2), (7, 1), (7, 2), (8, 2), (9, 1), (15, 2),
    (10, 4), (10, 5), (11, 4), (11, 5), (12, 6), (13, 6), (14, 7);

-- Una cuenta más por rol, para probar con otro evaluador y otro estudiante (RNF-03).
INSERT INTO cuenta (correo, clave, rol, usuario_id) VALUES
    ('carolina.restrepo@pascualbravo.edu.co', 'evaluador123', 'EVALUADOR', 3),
    ('laura.gomez@pascualbravo.edu.co', 'estudiante123', 'ESTUDIANTE', 6);

-- ───────── Equipos ─────────
INSERT INTO equipo (id, nombre) VALUES
    (2, 'Los Ingenieros'),
    (3, 'CodeBravo'),
    (4, 'Voltaje Cero'),
    (5, 'Byte Club'),
    (6, 'Scrum Masters'),
    (7, 'Equipo Soporte');

INSERT INTO equipo_integrante (equipo_id, usuario_id) VALUES
    (2, 6), (2, 7),
    (3, 8), (3, 9),
    (4, 10), (4, 11),
    (5, 12), (5, 13),
    (6, 14),
    (7, 15);

-- ───────── Ferias y rúbricas (HU-004) ─────────
-- La feria 1 (2026-2) ya existe en datos_demo.sql; aquí se le suman asignaturas.
INSERT INTO feria_asignatura (feria_id, asignatura_id) VALUES (1, 4), (1, 6), (1, 7);

-- Feria anterior, ya cerrada, con otra rúbrica: sirve para comparar ferias.
INSERT INTO feria (id, institucion_id, nombre, fecha_inicio, fecha_fin) VALUES
    (2, 1, 'Feria de Proyectos 2026-1', '2026-02-01', '2026-06-30');
INSERT INTO feria_asignatura (feria_id, asignatura_id) VALUES (2, 1), (2, 4), (2, 5);
INSERT INTO rubrica (id, feria_id, nota_minima, nota_maxima) VALUES (2, 2, 1.0, 5.0);
INSERT INTO criterio (id, rubrica_id, nombre, peso) VALUES
    (4, 2, 'Innovación', 0.4),
    (5, 2, 'Ejecución técnica', 0.4),
    (6, 2, 'Sustentación', 0.2);

-- ───────── Proyectos (HU-005) ─────────
INSERT INTO proyecto (id, equipo_id, feria_id, nombre, nombre_normalizado, descripcion,
                      modalidad, fecha_inscripcion) VALUES
    (2, 2, 1, 'Robot clasificador', 'robot clasificador',
     'Brazo robótico que separa piezas por color.', 'PIA', '2026-09-15'),
    (3, 3, 1, 'App de turnos', 'app de turnos',
     'Aplicación para pedir turnos en la cafetería.', 'PA', '2026-09-16'),
    (4, 4, 1, 'Medidor de consumo IoT', 'medidor de consumo iot',
     'Mide el consumo eléctrico de un salón y lo muestra en la web.', 'PIA', '2026-09-18'),
    (5, 5, 1, 'Sistema de inventario', 'sistema de inventario',
     'Control de entradas y salidas del almacén de laboratorio.', 'PA', '2026-09-20'),
    (6, 6, 1, 'Gestor de tareas ágil', 'gestor de tareas agil',
     'Tablero Kanban para equipos de proyecto.', 'PA', '2026-09-22'),
    (7, 7, 1, 'Chat de soporte', 'chat de soporte',
     'Chat para resolver dudas de los estudiantes nuevos.', 'PA', '2026-09-25'),
    (8, 3, 1, 'Tablero de control solar', 'tablero de control solar',
     'Calcula la eficiencia de los paneles solares del bloque B.', 'PA', '2026-09-26'),
    (9, 4, 2, 'Banco de pruebas de motores', 'banco de pruebas de motores',
     'Banco para medir torque y eficiencia de motores pequeños.', 'PA', '2026-03-10'),
    (10, 2, 2, 'Monitor de calidad del aire', 'monitor de calidad del aire',
     'Sensores de material particulado con tablero en tiempo real.', 'PIA', '2026-03-12'),
    (11, 5, 2, 'Biblioteca digital', 'biblioteca digital',
     'Catálogo en línea de la biblioteca del programa.', 'PA', '2026-03-15');

-- PA = una asignatura; PIA = dos o más (RN009).
INSERT INTO proyecto_asignatura (proyecto_id, asignatura_id) VALUES
    (2, 1), (2, 2),
    (3, 2),
    (4, 1), (4, 4),
    (5, 6),
    (6, 7),
    (7, 2),
    (8, 4),
    (9, 5),
    (10, 1), (10, 4),
    (11, 1);

-- ───────── Evaluaciones (HU-006, HU-007) ─────────
-- Estados variados para ver el reporte (HU-010): confirmadas de todos los niveles,
-- una en borrador (proyecto 4), una sin empezar (proyecto 6) y un proyecto sin
-- evaluador (proyecto 7). El proyecto 1 de datos_demo.sql sigue PENDIENTE.
INSERT INTO evaluacion (id, proyecto_id, evaluador_id, estado, puntaje_final,
                        fecha_confirmacion, retroalimentacion) VALUES
    (2, 2, 1, 'CONFIRMADA', 4.25, '2026-10-28T10:15:00-05:00', 'El robot clasifica bien por color; faltó medir el tiempo de respuesta.'),
    (3, 2, 3, 'CONFIRMADA', 3.45, '2026-10-29T16:40:00-05:00', 'Buena idea, pero el código no tiene pruebas y la base de datos no está normalizada.'),
    (4, 3, 3, 'CONFIRMADA', 4.85, '2026-10-29T11:05:00-05:00', 'Excelente: funciona completo, código limpio y una sustentación muy clara.'),
    (5, 4, 1, 'CONFIRMADA', 3.95, '2026-10-30T09:30:00-05:00', 'El prototipo mide bien; documentar mejor la conexión con el servidor.'),
    (6, 4, 4, 'BORRADOR', 3.15, NULL, 'Revisar la calibración del sensor antes de confirmar.'),
    (7, 5, 5, 'CONFIRMADA', 2.45, '2026-10-31T14:20:00-05:00', 'No se pudo demostrar el registro de salidas; el código no compila en otro equipo.'),
    (8, 6, 5, 'PENDIENTE', NULL, NULL, ''),
    (9, 8, 4, 'CONFIRMADA', 4.15, '2026-10-30T15:00:00-05:00', 'Muy buen cálculo de la eficiencia de los paneles; la presentación fue corta.'),
    (10, 9, 4, 'CONFIRMADA', 4.2, '2026-06-20T10:00:00-05:00', 'Montaje ordenado y mediciones repetibles.'),
    (11, 10, 1, 'CONFIRMADA', 4.7, '2026-06-21T09:00:00-05:00', 'Integra muy bien hardware y software; buen tablero de datos.'),
    (12, 10, 4, 'CONFIRMADA', 4.4, '2026-06-21T11:30:00-05:00', 'Sensores bien calibrados; la sustentación fue de las mejores.'),
    (13, 11, 3, 'CONFIRMADA', 3.3, '2026-06-22T08:45:00-05:00', 'Cumple lo básico; falta la búsqueda por autor y el control de préstamos.');

INSERT INTO calificacion_criterio (evaluacion_id, criterio_id, nota) VALUES
    (2, 1, 4.5), (2, 2, 4.0), (2, 3, 4.0),
    (3, 1, 3.5), (3, 2, 3.0), (3, 3, 4.0),
    (4, 1, 5.0), (4, 2, 4.5), (4, 3, 5.0),
    (5, 1, 4.0), (5, 2, 3.5), (5, 3, 4.5),
    (6, 1, 3.0), (6, 2, 3.5), (6, 3, 3.0),
    (7, 1, 2.5), (7, 2, 2.0), (7, 3, 3.0),
    (9, 1, 4.5), (9, 2, 4.0), (9, 3, 3.5),
    (10, 4, 4.0), (10, 5, 4.5), (10, 6, 4.0),
    (11, 4, 4.5), (11, 5, 5.0), (11, 6, 4.5),
    (12, 4, 4.0), (12, 5, 4.5), (12, 6, 5.0),
    (13, 4, 3.0), (13, 5, 3.5), (13, 6, 3.5);
