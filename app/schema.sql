-- Modelo de datos base de PDEP (PDEP-30).
-- Las restricciones UNIQUE son la segunda barrera contra duplicados: cubren el
-- caso en que dos solicitudes iguales pasan la validación al mismo tiempo.

DROP TABLE IF EXISTS calificacion_criterio;
DROP TABLE IF EXISTS evaluacion;
DROP TABLE IF EXISTS criterio;
DROP TABLE IF EXISTS rubrica;
DROP TABLE IF EXISTS proyecto_asignatura;
DROP TABLE IF EXISTS proyecto;
DROP TABLE IF EXISTS feria_asignatura;
DROP TABLE IF EXISTS feria;
DROP TABLE IF EXISTS equipo_integrante;
DROP TABLE IF EXISTS equipo;
DROP TABLE IF EXISTS usuario_asignatura;
DROP TABLE IF EXISTS usuario;
DROP TABLE IF EXISTS asignatura;
DROP TABLE IF EXISTS programa;
DROP TABLE IF EXISTS dominio_institucion;
DROP TABLE IF EXISTS institucion;

CREATE TABLE institucion (
    id      INTEGER PRIMARY KEY,
    nombre  TEXT NOT NULL,
    nit     TEXT NOT NULL UNIQUE,
    activa  INTEGER NOT NULL DEFAULT 1 CHECK (activa IN (0, 1))
);

CREATE TABLE dominio_institucion (
    institucion_id  INTEGER NOT NULL REFERENCES institucion (id),
    dominio         TEXT NOT NULL UNIQUE,
    PRIMARY KEY (institucion_id, dominio)
);

CREATE TABLE programa (
    id              INTEGER PRIMARY KEY,
    institucion_id  INTEGER NOT NULL REFERENCES institucion (id),
    codigo          TEXT NOT NULL UNIQUE,
    nombre          TEXT NOT NULL
);

CREATE TABLE asignatura (
    id          INTEGER PRIMARY KEY,
    programa_id INTEGER NOT NULL REFERENCES programa (id),
    codigo      TEXT NOT NULL UNIQUE,
    nombre      TEXT NOT NULL,
    semestre    INTEGER NOT NULL CHECK (semestre > 0)
);

CREATE TABLE usuario (
    id              INTEGER PRIMARY KEY,
    nombres         TEXT NOT NULL,
    correo          TEXT NOT NULL UNIQUE,
    rol             TEXT NOT NULL CHECK (rol IN ('ESTUDIANTE', 'DOCENTE')),
    programa_id     INTEGER NOT NULL REFERENCES programa (id),
    fecha_registro  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE usuario_asignatura (
    usuario_id      INTEGER NOT NULL REFERENCES usuario (id),
    asignatura_id   INTEGER NOT NULL REFERENCES asignatura (id),
    PRIMARY KEY (usuario_id, asignatura_id)
);

CREATE TABLE equipo (
    id      INTEGER PRIMARY KEY,
    nombre  TEXT NOT NULL
);

CREATE TABLE equipo_integrante (
    equipo_id   INTEGER NOT NULL REFERENCES equipo (id),
    usuario_id  INTEGER NOT NULL REFERENCES usuario (id),
    PRIMARY KEY (equipo_id, usuario_id)
);

CREATE TABLE feria (
    id              INTEGER PRIMARY KEY,
    institucion_id  INTEGER NOT NULL REFERENCES institucion (id),
    nombre          TEXT NOT NULL,
    fecha_inicio    TEXT NOT NULL,
    fecha_fin       TEXT NOT NULL,
    CHECK (fecha_fin >= fecha_inicio)
);

CREATE TABLE feria_asignatura (
    feria_id        INTEGER NOT NULL REFERENCES feria (id),
    asignatura_id   INTEGER NOT NULL REFERENCES asignatura (id),
    PRIMARY KEY (feria_id, asignatura_id)
);

CREATE TABLE proyecto (
    id                  INTEGER PRIMARY KEY,
    equipo_id           INTEGER NOT NULL REFERENCES equipo (id),
    feria_id            INTEGER NOT NULL REFERENCES feria (id),
    nombre              TEXT NOT NULL,
    nombre_normalizado  TEXT NOT NULL,
    descripcion         TEXT NOT NULL DEFAULT '',
    modalidad           TEXT NOT NULL CHECK (modalidad IN ('PA', 'PIA')),
    fecha_inscripcion   TEXT NOT NULL,
    UNIQUE (feria_id, equipo_id, nombre_normalizado)
);

CREATE TABLE proyecto_asignatura (
    proyecto_id     INTEGER NOT NULL REFERENCES proyecto (id),
    asignatura_id   INTEGER NOT NULL REFERENCES asignatura (id),
    PRIMARY KEY (proyecto_id, asignatura_id)
);

CREATE TABLE rubrica (
    id          INTEGER PRIMARY KEY,
    feria_id    INTEGER NOT NULL UNIQUE REFERENCES feria (id),
    nota_minima REAL NOT NULL DEFAULT 1.0,
    nota_maxima REAL NOT NULL DEFAULT 5.0,
    CHECK (nota_maxima > nota_minima)
);

CREATE TABLE criterio (
    id          INTEGER PRIMARY KEY,
    rubrica_id  INTEGER NOT NULL REFERENCES rubrica (id),
    nombre      TEXT NOT NULL,
    peso        REAL NOT NULL
);

CREATE TABLE evaluacion (
    id                  INTEGER PRIMARY KEY,
    proyecto_id         INTEGER NOT NULL REFERENCES proyecto (id),
    evaluador_id        INTEGER NOT NULL REFERENCES usuario (id),
    estado              TEXT NOT NULL DEFAULT 'PENDIENTE'
                        CHECK (estado IN ('PENDIENTE', 'BORRADOR', 'CONFIRMADA')),
    puntaje_final       REAL,
    fecha_confirmacion  TEXT,
    UNIQUE (proyecto_id, evaluador_id)
);

CREATE TABLE calificacion_criterio (
    evaluacion_id   INTEGER NOT NULL REFERENCES evaluacion (id),
    criterio_id     INTEGER NOT NULL REFERENCES criterio (id),
    nota            REAL NOT NULL,
    PRIMARY KEY (evaluacion_id, criterio_id)
);
