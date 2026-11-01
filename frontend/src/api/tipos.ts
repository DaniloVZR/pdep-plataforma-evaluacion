// Tipos que reflejan los JSON del backend (Flask). Si el backend cambia la
// forma de una respuesta, este es el único archivo que hay que ajustar.

export type Rol = 'ESTUDIANTE' | 'DOCENTE'
export type Modalidad = 'PA' | 'PIA'
export type EstadoEvaluacion = 'PENDIENTE' | 'BORRADOR' | 'CONFIRMADA'
/** Rol de la cuenta con la que se inicia sesión (RNF-03; actores del RTF1). */
export type RolCuenta = 'ADMINISTRADOR' | 'EVALUADOR' | 'ESTUDIANTE'

/** Cuerpo de error de cualquier respuesta 4xx/5xx. */
export interface ErrorRespuesta {
  codigo: string
  mensaje: string
}

// ───────────── Escrituras ─────────────

// HU-004 · POST /api/ferias (REQ-7): feria con asignaturas y criterios de evaluación
export interface SolicitudFeria {
  institucion_id: number
  nombre: string
  fecha_inicio: string // AAAA-MM-DD
  fecha_fin: string // AAAA-MM-DD
  asignatura_ids: number[]
  criterios: { nombre: string; peso: number }[] // pesos entre 0 y 1 que suman 1
}

export interface FeriaCreada {
  id: number
  nombre: string
  fecha_inicio: string
  fecha_fin: string
  asignatura_ids: number[]
}

// RNF-03 · POST /api/login
export interface SolicitudLogin {
  correo: string
  clave: string
}

/** Respuesta del inicio de sesión. El administrador no tiene usuario (usuario_id null). */
export interface RespuestaLogin {
  usuario_id: number | null
  nombre: string
  rol: RolCuenta
}

// HU-003 · POST /api/usuarios
export interface SolicitudUsuario {
  nombres: string
  correo: string
  rol: Rol
  programa_id: number
  asignatura_ids?: number[]
}

export interface Usuario {
  id: number
  nombres: string
  correo: string
  rol: Rol
  programa_id: number
  asignatura_ids: number[]
}

// HU-005 · POST /api/proyectos
export interface SolicitudProyecto {
  equipo_id: number
  feria_id: number
  nombre: string
  descripcion?: string
  modalidad: Modalidad
  asignatura_ids: number[]
}

export interface Proyecto {
  id: number
  equipo_id: number
  feria_id: number
  nombre: string
  modalidad: Modalidad
  asignatura_ids: number[]
  fecha_inscripcion: string // AAAA-MM-DD
}

// HU-007 · PUT /api/proyectos/<id>/evaluacion
export interface SolicitudCalificacion {
  evaluador_id: number
  /** Clave: id del criterio (como texto, así viaja en JSON). Valor: la nota. */
  notas: Record<string, number>
  /** false o ausente = borrador; true = confirmar y publicar el puntaje. */
  confirmar?: boolean
  /** HU-009 · Comentario para el equipo; lo ve el estudiante cuando se confirma. */
  retroalimentacion?: string
}

export interface Evaluacion {
  evaluacion_id: number
  proyecto_id: number
  estado: EstadoEvaluacion
  /** Solo viene con valor cuando la evaluación está CONFIRMADA. */
  puntaje_final: number | null
  fecha_confirmacion: string | null // ISO 8601 con zona horaria
  retroalimentacion: string
}

// HU-001 · POST /api/instituciones
export interface SolicitudInstitucion {
  nombre: string
  nit: string
  correo_contacto?: string
  telefono?: string
  /** Dominio del correo institucional (RN001), por ejemplo itm.edu.co. */
  dominio?: string
}

export interface InstitucionCreada {
  id: number
  nombre: string
  nit: string
  correo_contacto: string
  telefono: string
  dominio: string
}

// HU-001 · POST /api/facultades y POST /api/departamentos
export interface SolicitudUnidad {
  institucion_id: number
  nombre: string
}

/** Facultad o departamento (GET /api/facultades, GET /api/departamentos). */
export interface Unidad {
  id: number
  institucion_id: number
  nombre: string
}

// HU-001 · POST /api/programas (facultad, departamento o los dos)
export interface SolicitudPrograma {
  institucion_id: number
  codigo: string
  nombre: string
  facultad_id?: number
  departamento_id?: number
}

export interface ProgramaCreado {
  id: number
  institucion_id: number
  codigo: string
  nombre: string
  facultad_id: number | null
  departamento_id: number | null
}

// HU-002 · POST /api/asignaturas
export interface SolicitudAsignatura {
  programa_id: number
  codigo: string
  nombre: string
  semestre: number
}

export interface AsignaturaCreada {
  id: number
  programa_id: number
  codigo: string
  nombre: string
  semestre: number
}

// HU-006 · POST /api/proyectos/<id>/evaluadores
export interface SolicitudAsignacion {
  evaluador_ids: number[]
}

export interface Asignacion {
  proyecto_id: number
  asignados: { evaluacion_id: number; evaluador_id: number }[]
}

// ───────────── Consultas (GET, PDEP-35) ─────────────

/** GET /api/instituciones */
export interface Institucion {
  id: number
  nombre: string
  nit: string
  correo_contacto: string
  telefono: string
  dominios: string[]
}

export interface AsignaturaDePrograma {
  id: number
  codigo: string
  nombre: string
  semestre: number
}

/** GET /api/programas */
export interface Programa {
  id: number
  codigo: string
  nombre: string
  institucion_id: number
  facultad_id: number | null
  departamento_id: number | null
  asignaturas: AsignaturaDePrograma[]
}

/** GET /api/asignaturas[?programa_id=] (HU-002) */
export interface AsignaturaListada extends AsignaturaCreada {
  /** Nombre del programa al que está asociada. */
  programa: string
}

/** GET /api/usuarios[?rol=] */
export interface UsuarioResumen {
  id: number
  nombres: string
  correo: string
  rol: Rol
  programa_id: number
}

/** GET /api/equipos */
export interface Equipo {
  id: number
  nombre: string
  integrantes: { id: number; nombres: string }[]
}

/** GET /api/ferias */
export interface Feria {
  id: number
  institucion_id: number
  nombre: string
  fecha_inicio: string // AAAA-MM-DD
  fecha_fin: string // AAAA-MM-DD
  asignaturas: { id: number; codigo: string; nombre: string }[]
}

export interface Criterio {
  id: number
  nombre: string
  /** Fracción entre 0 y 1; todos suman 1. */
  peso: number
}

/** GET /api/ferias/<id>/rubrica */
export interface Rubrica {
  id: number
  feria_id: number
  nota_minima: number
  nota_maxima: number
  criterios: Criterio[]
}

/** GET /api/proyectos[?feria_id=] */
export interface ProyectoListado {
  id: number
  nombre: string
  descripcion: string
  modalidad: Modalidad
  fecha_inscripcion: string
  feria_id: number
  equipo_id: number
  equipo: string
  asignatura_ids: number[]
  /** Evaluadores asignados al proyecto (HU-006). */
  evaluadores: { id: number; nombres: string }[]
}

/** GET /api/evaluadores/carga (HU-006): proyectos asignados a cada docente. */
export interface CargaEvaluador {
  id: number
  nombres: string
  correo: string
  asignados: number
  pendientes: number
  borradores: number
  confirmadas: number
}

/** GET /api/evaluaciones?evaluador_id= */
export interface EvaluacionAsignada {
  evaluacion_id: number
  proyecto_id: number
  proyecto: string
  feria_id: number
  feria: string
  estado: EstadoEvaluacion
  /** Solo viene con valor cuando la evaluación está CONFIRMADA. */
  puntaje_final: number | null
  fecha_confirmacion: string | null
  /** Comentario del propio evaluador (también en borrador). */
  retroalimentacion: string
  /** Notas guardadas por criterio (clave: id del criterio); vacío si aún no calificó. */
  notas: Record<string, number>
}

/** Evaluación de un proyecto tal como la ve el estudiante (HU-009, RN007). */
export interface ResultadoEvaluacion {
  evaluacion_id: number
  evaluador: string
  estado: EstadoEvaluacion
  /** null mientras la evaluación no esté CONFIRMADA. */
  puntaje_final: number | null
  /** null mientras la evaluación no esté CONFIRMADA; "" si el evaluador no escribió nada. */
  retroalimentacion: string | null
  fecha_confirmacion: string | null
}

/** GET /api/resultados?estudiante_id= (HU-009) */
export interface ResultadoProyecto {
  proyecto_id: number
  proyecto: string
  feria: string
  equipo: string
  evaluaciones: ResultadoEvaluacion[]
}
