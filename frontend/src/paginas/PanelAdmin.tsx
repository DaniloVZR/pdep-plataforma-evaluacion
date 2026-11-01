import {
  BookOpen,
  CalendarDays,
  ClipboardCheck,
  FileText,
  FolderKanban,
  GraduationCap,
  Landmark,
  ListChecks,
  Network,
  UserCheck,
  UserRound,
  Users,
  type LucideIcon,
} from 'lucide-react'
import { useState, type CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import {
  listarCargaEvaluadores,
  listarFerias,
  listarInstituciones,
  listarProgramas,
  listarProyectos,
  listarUsuarios,
} from '../api/endpoints.ts'
import { useConsulta } from '../hooks/useConsulta.ts'

interface Modulo {
  titulo: string
  subtitulo: string
  etiqueta: string
  color: string
  icono: LucideIcon
  /** Pantalla a la que lleva; sin ruta, la pantalla aún no existe. */
  ruta?: string
}

// Funciones estables: useConsulta vuelve a consultar si cambia la referencia.
const cargarUsuarios = () => listarUsuarios()
const cargarProgramas = () => listarProgramas()
const cargarFerias = () => listarFerias()
const cargarProyectos = () => listarProyectos()
const cargarInstituciones = () => listarInstituciones()
const cargarCarga = () => listarCargaEvaluadores()

/** "3 Registrados" si ya se conoce la cantidad; solo "Registrados" mientras carga o si falla. */
function conteo(n: number | null, singular: string, plural: string): string {
  if (n === null) return plural
  return `${n} ${n === 1 ? singular : plural}`
}

/** Fecha de hoy como AAAA-MM-DD en la zona horaria del navegador. */
const fechaDeHoy = () => new Date().toLocaleDateString('sv-SE')

export function PanelAdmin() {
  const usuarios = useConsulta(cargarUsuarios)
  const programas = useConsulta(cargarProgramas)
  const ferias = useConsulta(cargarFerias)
  const proyectos = useConsulta(cargarProyectos)
  const instituciones = useConsulta(cargarInstituciones)
  const carga = useConsulta(cargarCarga)
  const [aviso, setAviso] = useState('')
  const [hoy] = useState(fechaDeHoy)

  const estudiantes = usuarios.datos?.filter((u) => u.rol === 'ESTUDIANTE').length ?? null
  const docentes = usuarios.datos?.filter((u) => u.rol === 'DOCENTE').length ?? null
  const asignaturas = programas.datos?.reduce((suma, p) => suma + p.asignaturas.length, 0) ?? null
  const conEvaluaciones = carga.datos?.filter((e) => e.asignados > 0).length ?? null
  const activas =
    ferias.datos?.filter((f) => f.fecha_inicio <= hoy && hoy <= f.fecha_fin).length ?? null

  const modulos: Modulo[] = [
    { titulo: 'Instituciones', subtitulo: 'Gestión principal', etiqueta: conteo(instituciones.datos?.length ?? null, 'Registrada', 'Registradas'), color: '#0A3D73', icono: Landmark, ruta: '/estructura/instituciones' },
    { titulo: 'Facultades y Departamentos', subtitulo: 'Estructura interna', etiqueta: 'Configuración', color: '#6D28D9', icono: Network, ruta: '/estructura/facultades' },
    { titulo: 'Programas', subtitulo: 'Programas académicos', etiqueta: conteo(programas.datos?.length ?? null, 'Activo', 'Activos'), color: '#0F766E', icono: GraduationCap, ruta: '/estructura/programas' },
    { titulo: 'Asignaturas', subtitulo: 'Materias vinculadas', etiqueta: conteo(asignaturas, 'Activa', 'Activas'), color: '#C2410C', icono: BookOpen },
    { titulo: 'Estudiantes', subtitulo: 'Participantes de proyectos', etiqueta: conteo(estudiantes, 'Registrado', 'Registrados'), color: '#1D4ED8', icono: Users, ruta: '/usuarios/nuevo' },
    { titulo: 'Docentes', subtitulo: 'Plantilla docente', etiqueta: conteo(docentes, 'Registrado', 'Registrados'), color: '#BE185D', icono: UserRound, ruta: '/usuarios/nuevo' },
    { titulo: 'Evaluadores', subtitulo: 'Jurados asignados', etiqueta: conteo(conEvaluaciones, 'Con proyectos', 'Con proyectos'), color: '#047857', icono: UserCheck, ruta: '/asignaciones' },
    { titulo: 'Ferias / Eventos', subtitulo: 'Organización de periodos', etiqueta: conteo(activas, 'Activa', 'Activas'), color: '#A21CAF', icono: CalendarDays, ruta: '/ferias' },
    { titulo: 'Proyectos', subtitulo: 'Trabajos inscritos', etiqueta: conteo(proyectos.datos?.length ?? null, 'Inscrito', 'Inscritos'), color: '#0E7490', icono: FolderKanban, ruta: '/proyectos' },
    { titulo: 'Rúbricas', subtitulo: 'Criterios de evaluación', etiqueta: 'Configurables', color: '#4D7C0F', icono: ListChecks, ruta: '/ferias' },
    { titulo: 'Evaluaciones', subtitulo: 'Calificaciones y notas', etiqueta: 'Seguimiento', color: '#4338CA', icono: ClipboardCheck },
    { titulo: 'Reportes', subtitulo: 'Resultados consolidados', etiqueta: 'Generar PDF/Excel', color: '#374151', icono: FileText },
  ]

  return (
    <section>
      <div className="bienvenida">
        <h1>Bienvenido, Administrador</h1>
        <p>Gestión completa del sistema de evaluación de proyectos</p>
      </div>

      {aviso && (
        <p className="aviso aviso-info" role="status">
          {aviso}
        </p>
      )}

      <ul className="modulos">
        {modulos.map(({ titulo, subtitulo, etiqueta, color, icono: Icono, ruta }) => {
          const contenido = (
            <>
              <span className="modulo-icono">
                <Icono size={26} aria-hidden="true" />
              </span>
              <span className="modulo-titulo">{titulo}</span>
              <span className="modulo-subtitulo">{subtitulo}</span>
              <span className="modulo-etiqueta">{etiqueta}</span>
            </>
          )
          const estilo = { '--tarjeta': color } as CSSProperties
          return (
            <li key={titulo}>
              {ruta ? (
                <Link to={ruta} className="modulo" style={estilo}>
                  {contenido}
                </Link>
              ) : (
                <button
                  type="button"
                  className="modulo"
                  style={estilo}
                  onClick={() => setAviso(`«${titulo}» todavía no tiene pantalla. Se habilita en un próximo paso.`)}
                >
                  {contenido}
                </button>
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}
