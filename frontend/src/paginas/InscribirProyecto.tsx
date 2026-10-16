import { CalendarDays, Send } from 'lucide-react'
import { useId, useState, type SyntheticEvent } from 'react'
import { Link } from 'react-router-dom'
import type { ErrorApi } from '../api/cliente.ts'
import { inscribirProyecto, listarEquipos, listarFerias } from '../api/endpoints.ts'
import type { Feria, Modalidad, Proyecto } from '../api/tipos.ts'
import { Cargando, MensajeError } from '../componentes/Estados.tsx'
import { useConsulta } from '../hooks/useConsulta.ts'
import { useSesion } from '../sesion/contexto.ts'
import { comoErrorApi, ETIQUETA_MODALIDAD, fechaDeHoy, formatearFecha } from '../utilidades.ts'

const cargarEquipos = () => listarEquipos()
const cargarFerias = () => listarFerias()

function estadoPlazo(feria: Feria, hoy: string) {
  if (hoy < feria.fecha_inicio) return { texto: 'Aún no abre', clase: 'insignia-gris' }
  if (hoy > feria.fecha_fin) return { texto: 'Plazo vencido', clase: 'insignia-roja' }
  return { texto: 'Inscripción abierta', clase: 'insignia-verde' }
}

/**
 * HU-005 · Un estudiante inscribe el proyecto de su equipo en una feria.
 * El plazo (RN003) y el nombre duplicado (RN002) los valida el backend: aunque la
 * feria esté cerrada se deja enviar, para que el rechazo y su mensaje sean visibles.
 */
export function InscribirProyecto() {
  const id = useId()
  const { sesion } = useSesion()
  const equipos = useConsulta(cargarEquipos)
  const ferias = useConsulta(cargarFerias)
  const [hoy] = useState(fechaDeHoy)

  const [equipoId, setEquipoId] = useState('')
  const [feriaId, setFeriaId] = useState('')
  const [nombre, setNombre] = useState('')
  const [descripcion, setDescripcion] = useState('')
  const [modalidad, setModalidad] = useState<Modalidad>('PA')
  const [asignaturaIds, setAsignaturaIds] = useState<number[]>([])

  const [intentado, setIntentado] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [errorServidor, setErrorServidor] = useState<ErrorApi | null>(null)
  const [inscrito, setInscrito] = useState<Proyecto | null>(null)

  // Solo los equipos en los que está el estudiante de la sesión.
  const misEquipos =
    equipos.datos?.filter((e) => e.integrantes.some((i) => i.id === sesion?.usuarioId)) ?? []
  const equipoElegido = equipoId || (misEquipos.length === 1 ? String(misEquipos[0].id) : '')
  const feria = ferias.datos?.find((f) => String(f.id) === feriaId)

  const errores = {
    equipo: equipoElegido ? '' : 'Elige el equipo que inscribe el proyecto.',
    feria: feriaId ? '' : 'Elige la feria.',
    nombre: nombre.trim() ? '' : 'Escribe el nombre del proyecto.',
    asignaturas:
      asignaturaIds.length === 0
        ? 'Elige al menos una asignatura.'
        : modalidad === 'PIA' && asignaturaIds.length < 2
          ? 'Un Proyecto Integrador (PIA) requiere dos o más asignaturas.'
          : '',
  }
  const hayErrores = Object.values(errores).some(Boolean)
  const mostrar = (campo: keyof typeof errores) => intentado && errores[campo] !== ''

  function cambiarModalidad(nueva: Modalidad) {
    setModalidad(nueva)
    // Un PA lleva una sola asignatura: al cambiar se conserva como mucho la primera.
    if (nueva === 'PA') setAsignaturaIds((actuales) => actuales.slice(0, 1))
  }

  function elegirAsignatura(asignaturaId: number) {
    if (modalidad === 'PA') {
      setAsignaturaIds([asignaturaId])
      return
    }
    setAsignaturaIds((actuales) =>
      actuales.includes(asignaturaId)
        ? actuales.filter((a) => a !== asignaturaId)
        : [...actuales, asignaturaId],
    )
  }

  async function enviar(evento: SyntheticEvent<HTMLFormElement>) {
    evento.preventDefault()
    setIntentado(true)
    setInscrito(null)
    setErrorServidor(null)
    if (hayErrores) return

    setEnviando(true)
    try {
      const proyecto = await inscribirProyecto({
        equipo_id: Number(equipoElegido),
        feria_id: Number(feriaId),
        nombre: nombre.trim(),
        descripcion: descripcion.trim() || undefined,
        modalidad,
        asignatura_ids: asignaturaIds,
      })
      setInscrito(proyecto)
      setNombre('')
      setDescripcion('')
      setAsignaturaIds([])
      setIntentado(false)
    } catch (causa) {
      setErrorServidor(comoErrorApi(causa))
    } finally {
      setEnviando(false)
    }
  }

  if (equipos.cargando || ferias.cargando) return <Cargando texto="Cargando equipos y ferias…" />
  if (equipos.error) return <MensajeError error={equipos.error} alReintentar={equipos.recargar} />
  if (ferias.error) return <MensajeError error={ferias.error} alReintentar={ferias.recargar} />

  return (
    <section className="pantalla">
      <div className="bienvenida">
        <h1>Inscribir proyecto</h1>
        <p>Registra el proyecto de tu equipo en una feria para que pueda ser evaluado.</p>
      </div>

      {inscrito && (
        <div className="aviso aviso-exito" role="status">
          <p>
            El proyecto <strong>{inscrito.nombre}</strong> quedó inscrito el{' '}
            {formatearFecha(inscrito.fecha_inscripcion)}.
          </p>
          <Link to="/proyectos">Ver proyectos inscritos</Link>
        </div>
      )}
      {errorServidor && <MensajeError error={errorServidor} />}

      {misEquipos.length === 0 ? (
        <div className="aviso aviso-info">
          <p>
            No perteneces a ningún equipo todavía. Con «Ver como» elige un estudiante que tenga
            equipo (en los datos demo: Estudiante Demo).
          </p>
        </div>
      ) : (
        <form className="tarjeta" onSubmit={enviar} noValidate>
          <div className="rejilla-2">
            <div className="campo">
              <label htmlFor={`${id}-equipo`}>Equipo</label>
              <select
                id={`${id}-equipo`}
                value={equipoElegido}
                onChange={(e) => setEquipoId(e.target.value)}
                aria-invalid={mostrar('equipo')}
              >
                <option value="">Selecciona tu equipo</option>
                {misEquipos.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.nombre}
                  </option>
                ))}
              </select>
              {mostrar('equipo') && <p className="campo-error">{errores.equipo}</p>}
            </div>

            <div className="campo">
              <label htmlFor={`${id}-feria`}>Feria</label>
              <select
                id={`${id}-feria`}
                value={feriaId}
                onChange={(e) => {
                  setFeriaId(e.target.value)
                  setAsignaturaIds([])
                }}
                aria-invalid={mostrar('feria')}
              >
                <option value="">Selecciona una feria</option>
                {ferias.datos?.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.nombre}
                  </option>
                ))}
              </select>
              {mostrar('feria') && <p className="campo-error">{errores.feria}</p>}
              {feria && (
                <p className="campo-ayuda fila-icono">
                  <CalendarDays size={16} aria-hidden="true" />
                  {formatearFecha(feria.fecha_inicio)} – {formatearFecha(feria.fecha_fin)}
                  <span className={`insignia ${estadoPlazo(feria, hoy).clase}`}>
                    {estadoPlazo(feria, hoy).texto}
                  </span>
                </p>
              )}
            </div>
          </div>

          <div className="campo">
            <label htmlFor={`${id}-nombre`}>Nombre del proyecto</label>
            <input
              id={`${id}-nombre`}
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              aria-invalid={mostrar('nombre')}
            />
            {mostrar('nombre') && <p className="campo-error">{errores.nombre}</p>}
          </div>

          <div className="campo">
            <label htmlFor={`${id}-descripcion`}>
              Descripción <small className="texto-suave">(opcional)</small>
            </label>
            <textarea
              id={`${id}-descripcion`}
              rows={3}
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
            />
          </div>

          <fieldset>
            <legend className="tarjeta-subtitulo">Modalidad</legend>
            <div className="selector-segmentado">
              {(['PA', 'PIA'] as const).map((m) => (
                <label key={m} className={modalidad === m ? 'activo' : ''}>
                  <input
                    type="radio"
                    name={`${id}-modalidad`}
                    checked={modalidad === m}
                    onChange={() => cambiarModalidad(m)}
                  />
                  {ETIQUETA_MODALIDAD[m]}
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend className="tarjeta-subtitulo">
              {modalidad === 'PA' ? 'Asignatura' : 'Asignaturas (dos o más)'}
            </legend>
            {!feria ? (
              <p className="estado">Elige primero la feria para ver sus asignaturas participantes.</p>
            ) : (
              <ul className="opciones">
                {feria.asignaturas.map((a) => (
                  <li key={a.id}>
                    <label className="opcion">
                      <input
                        type={modalidad === 'PA' ? 'radio' : 'checkbox'}
                        name={`${id}-asignatura`}
                        checked={asignaturaIds.includes(a.id)}
                        onChange={() => elegirAsignatura(a.id)}
                      />
                      <span>
                        {a.nombre} <small>{a.codigo}</small>
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
            )}
            {mostrar('asignaturas') && <p className="campo-error">{errores.asignaturas}</p>}
          </fieldset>

          <div className="acciones">
            <button type="submit" className="boton boton-azul" disabled={enviando}>
              <Send size={18} aria-hidden="true" />
              {enviando ? 'Inscribiendo…' : 'Inscribir proyecto'}
            </button>
          </div>
        </form>
      )}
    </section>
  )
}
