// Todos los endpoints que existen hoy en el backend, conectados de verdad.
import { api } from './cliente'
import type {
  Equipo,
  Evaluacion,
  EvaluacionAsignada,
  Feria,
  Programa,
  Proyecto,
  ProyectoListado,
  Rol,
  Rubrica,
  SolicitudCalificacion,
  SolicitudProyecto,
  SolicitudUsuario,
  Usuario,
  UsuarioResumen,
} from './tipos'

// ───────────── Escrituras ─────────────

/** HU-003 · Registrar un estudiante o docente. */
export const registrarUsuario = (datos: SolicitudUsuario) =>
  api.post<Usuario>('/api/usuarios', datos)

/** HU-005 · Inscribir un proyecto en una feria. */
export const inscribirProyecto = (datos: SolicitudProyecto) =>
  api.post<Proyecto>('/api/proyectos', datos)

/** HU-007 · Calificar un proyecto (borrador o confirmada). */
export const calificarProyecto = (proyectoId: number, datos: SolicitudCalificacion) =>
  api.put<Evaluacion>(`/api/proyectos/${proyectoId}/evaluacion`, datos)

// ───────────── Consultas ─────────────

export const listarProgramas = () => api.get<Programa[]>('/api/programas')

export const listarUsuarios = (rol?: Rol) =>
  api.get<UsuarioResumen[]>(rol ? `/api/usuarios?rol=${rol}` : '/api/usuarios')

export const listarEquipos = () => api.get<Equipo[]>('/api/equipos')

export const listarFerias = () => api.get<Feria[]>('/api/ferias')

/** 404 si la feria no existe; 422 (`rubrica_no_encontrada`) si no tiene rúbrica. */
export const obtenerRubrica = (feriaId: number) =>
  api.get<Rubrica>(`/api/ferias/${feriaId}/rubrica`)

export const listarProyectos = (feriaId?: number) =>
  api.get<ProyectoListado[]>(feriaId ? `/api/proyectos?feria_id=${feriaId}` : '/api/proyectos')

export const listarEvaluaciones = (evaluadorId: number) =>
  api.get<EvaluacionAsignada[]>(`/api/evaluaciones?evaluador_id=${evaluadorId}`)
