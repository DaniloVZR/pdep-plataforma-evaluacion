// Todos los endpoints que existen hoy en el backend, conectados de verdad.
import { api } from './cliente'
import type {
  Asignacion,
  AsignaturaCreada,
  AsignaturaListada,
  CargaEvaluador,
  Equipo,
  Evaluacion,
  EvaluacionAsignada,
  Feria,
  FeriaCreada,
  Institucion,
  InstitucionCreada,
  Programa,
  ProgramaCreado,
  Proyecto,
  ProyectoListado,
  RespuestaLogin,
  ResultadoProyecto,
  Rol,
  Rubrica,
  SolicitudAsignacion,
  SolicitudAsignatura,
  SolicitudCalificacion,
  SolicitudFeria,
  SolicitudInstitucion,
  SolicitudLogin,
  SolicitudPrograma,
  SolicitudProyecto,
  SolicitudUnidad,
  SolicitudUsuario,
  Unidad,
  Usuario,
  UsuarioResumen,
} from './tipos'

// ───────────── Escrituras ─────────────

/** HU-004 · Crear una feria con sus asignaturas y su rúbrica (REQ-7). */
export const crearFeria = (datos: SolicitudFeria) => api.post<FeriaCreada>('/api/ferias', datos)

/** RNF-03 · Iniciar sesión con correo y clave; responde el usuario, su nombre y su rol. */
export const iniciarSesion = (datos: SolicitudLogin) =>
  api.post<RespuestaLogin>('/api/login', datos)

/** HU-001 · Registrar una institución. */
export const registrarInstitucion = (datos: SolicitudInstitucion) =>
  api.post<InstitucionCreada>('/api/instituciones', datos)

/** HU-001 · Registrar una facultad de una institución. */
export const registrarFacultad = (datos: SolicitudUnidad) =>
  api.post<Unidad>('/api/facultades', datos)

/** HU-001 · Registrar un departamento de una institución. */
export const registrarDepartamento = (datos: SolicitudUnidad) =>
  api.post<Unidad>('/api/departamentos', datos)

/** HU-001 · Registrar un programa asociado a una facultad o un departamento. */
export const registrarPrograma = (datos: SolicitudPrograma) =>
  api.post<ProgramaCreado>('/api/programas', datos)

/** HU-002 · Registrar una asignatura asociada a un programa académico (REQ-4). */
export const registrarAsignatura = (datos: SolicitudAsignatura) =>
  api.post<AsignaturaCreada>('/api/asignaturas', datos)

/** HU-003 · Registrar un estudiante o docente. */
export const registrarUsuario = (datos: SolicitudUsuario) =>
  api.post<Usuario>('/api/usuarios', datos)

/** HU-005 · Inscribir un proyecto en una feria. */
export const inscribirProyecto = (datos: SolicitudProyecto) =>
  api.post<Proyecto>('/api/proyectos', datos)

/** HU-006 · Asignar uno o varios evaluadores a un proyecto. */
export const asignarEvaluadores = (proyectoId: number, datos: SolicitudAsignacion) =>
  api.post<Asignacion>(`/api/proyectos/${proyectoId}/evaluadores`, datos)

/** HU-007 · Calificar un proyecto (borrador o confirmada). */
export const calificarProyecto = (proyectoId: number, datos: SolicitudCalificacion) =>
  api.put<Evaluacion>(`/api/proyectos/${proyectoId}/evaluacion`, datos)

// ───────────── Consultas ─────────────

export const listarInstituciones = () => api.get<Institucion[]>('/api/instituciones')

export const listarFacultades = (institucionId: number) =>
  api.get<Unidad[]>(`/api/facultades?institucion_id=${institucionId}`)

export const listarDepartamentos = (institucionId: number) =>
  api.get<Unidad[]>(`/api/departamentos?institucion_id=${institucionId}`)

export const listarProgramas = () => api.get<Programa[]>('/api/programas')

/** HU-002 · Asignaturas de un programa; 404 si el programa no existe. */
export const listarAsignaturas = (programaId: number) =>
  api.get<AsignaturaListada[]>(`/api/asignaturas?programa_id=${programaId}`)

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

/** HU-006 · Cantidad de proyectos asignados a cada docente. */
export const listarCargaEvaluadores = () => api.get<CargaEvaluador[]>('/api/evaluadores/carga')

/** HU-009 · Proyectos del estudiante; puntaje y retroalimentación solo si está confirmada. */
export const consultarResultados = (estudianteId: number) =>
  api.get<ResultadoProyecto[]>(`/api/resultados?estudiante_id=${estudianteId}`)
