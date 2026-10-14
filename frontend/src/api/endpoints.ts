// Los tres endpoints que ya existen en el backend, conectados de verdad.
import { api } from './cliente'
import type {
  Evaluacion,
  Proyecto,
  SolicitudCalificacion,
  SolicitudProyecto,
  SolicitudUsuario,
  Usuario,
} from './tipos'

/** HU-003 · Registrar un estudiante o docente. */
export const registrarUsuario = (datos: SolicitudUsuario) =>
  api.post<Usuario>('/api/usuarios', datos)

/** HU-005 · Inscribir un proyecto en una feria. */
export const inscribirProyecto = (datos: SolicitudProyecto) =>
  api.post<Proyecto>('/api/proyectos', datos)

/** HU-007 · Calificar un proyecto (borrador o confirmada). */
export const calificarProyecto = (proyectoId: number, datos: SolicitudCalificacion) =>
  api.put<Evaluacion>(`/api/proyectos/${proyectoId}/evaluacion`, datos)
