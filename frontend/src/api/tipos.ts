// Tipos que reflejan los JSON del backend (Flask). Si el backend cambia la
// forma de una respuesta, este es el único archivo que hay que ajustar.

export type Rol = 'ESTUDIANTE' | 'DOCENTE'
export type Modalidad = 'PA' | 'PIA'
export type EstadoEvaluacion = 'PENDIENTE' | 'BORRADOR' | 'CONFIRMADA'

/** Cuerpo de error de cualquier respuesta 4xx/5xx. */
export interface ErrorRespuesta {
  codigo: string
  mensaje: string
}

// ───────────── Escrituras ─────────────

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
}

export interface Evaluacion {
  evaluacion_id: number
  proyecto_id: number
  estado: EstadoEvaluacion
  /** Solo viene con valor cuando la evaluación está CONFIRMADA. */
  puntaje_final: number | null
  fecha_confirmacion: string | null // ISO 8601 con zona horaria
}

// ───────────── Consultas (GET, PDEP-35) ─────────────

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
  asignaturas: AsignaturaDePrograma[]
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
}
