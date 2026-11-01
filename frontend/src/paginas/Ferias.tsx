import { CalendarDays, Plus, Trash2 } from 'lucide-react'
import { useId, useState, type SyntheticEvent } from 'react'
import { Link } from 'react-router-dom'
import type { ErrorApi } from '../api/cliente.ts'
import { crearFeria, listarFerias, listarProgramas } from '../api/endpoints.ts'
import { Cargando, MensajeError } from '../componentes/Estados.tsx'
import { SelectorInstitucion } from '../componentes/MenuEstructura.tsx'
import { useConsulta } from '../hooks/useConsulta.ts'
import { useInstitucionElegida } from '../hooks/useInstitucionElegida.ts'
import { comoErrorApi, formatearFecha } from '../utilidades.ts'

const cargarFerias = () => listarFerias()
const cargarProgramas = () => listarProgramas()

interface CriterioFormulario {
  clave: number
  nombre: string
  peso: string // porcentaje escrito por el usuario, por ejemplo "40"
}

const CRITERIOS_INICIALES: CriterioFormulario[] = [
  { clave: 1, nombre: '', peso: '' },
  { clave: 2, nombre: '', peso: '' },
]

/**
 * HU-004 · REQ-7: crear una feria con sus fechas, asignaturas participantes y criterios
 * de evaluación. Los pesos se escriben en porcentaje y se envían como fracción (40 → 0.4).
 * El backend valida que el fin sea posterior al inicio y que los pesos sumen 100 %.
 */
export function Ferias() {
  const id = useId()
  const { instituciones, institucion, elegir } = useInstitucionElegida()
  const institucionId = institucion?.id ?? 0
  const ferias = useConsulta(cargarFerias)
  const programas = useConsulta(cargarProgramas)

  const [nombre, setNombre] = useState('')
  const [inicio, setInicio] = useState('')
  const [fin, setFin] = useState('')
  const [asignaturaIds, setAsignaturaIds] = useState<number[]>([])
  const [criterios, setCriterios] = useState<CriterioFormulario[]>(CRITERIOS_INICIALES)
  const [siguienteClave, setSiguienteClave] = useState(3)
  const [intentado, setIntentado] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<ErrorApi | null>(null)
  const [exito, setExito] = useState('')

  const programasPropios = programas.datos?.filter((p) => p.institucion_id === institucionId) ?? []
  const asignaturasDisponibles = programasPropios.flatMap((p) =>
    p.asignaturas.map((a) => ({ ...a, programa: p.codigo })),
  )
  const feriasPropias = ferias.datos?.filter((f) => f.institucion_id === institucionId) ?? []

  const sumaPesos = criterios.reduce((total, c) => total + (Number(c.peso) || 0), 0)
  const errores = {
    nombre: nombre.trim() ? '' : 'Escribe el nombre de la feria.',
    fechas:
      !inicio || !fin
        ? 'Elige la fecha de inicio y la de fin.'
        : fin <= inicio
          ? 'La fecha de fin debe ser posterior a la de inicio.'
          : '',
    asignaturas: asignaturaIds.length ? '' : 'Elige al menos una asignatura participante.',
    criterios: criterios.every((c) => c.nombre.trim() && Number(c.peso) > 0)
      ? Math.abs(sumaPesos - 100) <= 0.0001
        ? ''
        : `Los pesos deben sumar 100 %. Ahora suman ${Number(sumaPesos.toFixed(2))} %.`
      : 'Cada criterio necesita un nombre y un peso mayor que 0.',
  }
  const mostrar = (campo: keyof typeof errores) => intentado && errores[campo] !== ''

  function cambiarInstitucion(nueva: number) {
    elegir(nueva)
    setAsignaturaIds([])
  }

  function alternarAsignatura(asignaturaId: number) {
    setAsignaturaIds((actuales) =>
      actuales.includes(asignaturaId)
        ? actuales.filter((a) => a !== asignaturaId)
        : [...actuales, asignaturaId],
    )
  }

  function cambiarCriterio(clave: number, campo: 'nombre' | 'peso', valor: string) {
    setCriterios((actuales) => actuales.map((c) => (c.clave === clave ? { ...c, [campo]: valor } : c)))
  }

  function agregarCriterio() {
    setCriterios((actuales) => [...actuales, { clave: siguienteClave, nombre: '', peso: '' }])
    setSiguienteClave((c) => c + 1)
  }

  function quitarCriterio(clave: number) {
    setCriterios((actuales) => actuales.filter((c) => c.clave !== clave))
  }

  function limpiar() {
    setNombre('')
    setInicio('')
    setFin('')
    setAsignaturaIds([])
    setCriterios(CRITERIOS_INICIALES)
    setIntentado(false)
  }

  async function guardar(evento: SyntheticEvent<HTMLFormElement>) {
    evento.preventDefault()
    setIntentado(true)
    setError(null)
    setExito('')
    if (Object.values(errores).some(Boolean)) return
    setEnviando(true)
    try {
      const creada = await crearFeria({
        institucion_id: institucionId,
        nombre: nombre.trim(),
        fecha_inicio: inicio,
        fecha_fin: fin,
        asignatura_ids: asignaturaIds,
        criterios: criterios.map((c) => ({ nombre: c.nombre.trim(), peso: Number(c.peso) / 100 })),
      })
      setExito(
        `La feria «${creada.nombre}» quedó creada del ${formatearFecha(creada.fecha_inicio)} ` +
          `al ${formatearFecha(creada.fecha_fin)}, con su rúbrica lista para calificar.`,
      )
      limpiar()
      ferias.recargar()
    } catch (causa) {
      setError(comoErrorApi(causa))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section className="pantalla pila">
      <div className="bienvenida">
        <h1>Ferias y eventos</h1>
        <p>Crea una feria con sus fechas, asignaturas participantes y criterios de evaluación.</p>
      </div>

      {instituciones.cargando ? (
        <Cargando texto="Cargando instituciones…" />
      ) : instituciones.error ? (
        <MensajeError error={instituciones.error} alReintentar={instituciones.recargar} />
      ) : institucion === null ? (
        <div className="aviso aviso-info">
          <p>
            Primero <Link to="/estructura/instituciones">registra una institución</Link>.
          </p>
        </div>
      ) : (
        <>
          <SelectorInstitucion
            id={`${id}-institucion`}
            instituciones={instituciones.datos ?? []}
            elegida={institucion}
            alElegir={cambiarInstitucion}
          />

          {exito && (
            <p className="aviso aviso-exito" role="status">
              {exito}
            </p>
          )}
          {error && <MensajeError error={error} />}

          <form className="tarjeta" onSubmit={guardar} noValidate>
            <h2 className="tarjeta-subtitulo fila-icono">
              <CalendarDays size={18} aria-hidden="true" /> Nueva feria
            </h2>

            <div className="campo">
              <label htmlFor={`${id}-nombre`}>Nombre</label>
              <input
                id={`${id}-nombre`}
                type="text"
                placeholder="Feria de Proyectos 2027-1"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                aria-invalid={mostrar('nombre')}
              />
              {mostrar('nombre') && <p className="campo-error">{errores.nombre}</p>}
            </div>

            <div className="rejilla-2">
              <div className="campo">
                <label htmlFor={`${id}-inicio`}>Fecha de inicio</label>
                <input
                  id={`${id}-inicio`}
                  type="date"
                  value={inicio}
                  onChange={(e) => setInicio(e.target.value)}
                  aria-invalid={mostrar('fechas')}
                />
              </div>
              <div className="campo">
                <label htmlFor={`${id}-fin`}>Fecha de fin</label>
                <input
                  id={`${id}-fin`}
                  type="date"
                  min={inicio || undefined}
                  value={fin}
                  onChange={(e) => setFin(e.target.value)}
                  aria-invalid={mostrar('fechas')}
                />
              </div>
            </div>
            {mostrar('fechas') && <p className="campo-error">{errores.fechas}</p>}

            <fieldset>
              <legend className="tarjeta-subtitulo">Asignaturas participantes</legend>
              {programas.cargando ? (
                <Cargando texto="Cargando asignaturas…" />
              ) : programas.error ? (
                <MensajeError error={programas.error} alReintentar={programas.recargar} />
              ) : asignaturasDisponibles.length === 0 ? (
                <p className="estado">
                  Esta institución no tiene asignaturas registradas en sus programas.
                </p>
              ) : (
                <ul className="opciones">
                  {asignaturasDisponibles.map((a) => (
                    <li key={a.id}>
                      <label className="opcion">
                        <input
                          type="checkbox"
                          checked={asignaturaIds.includes(a.id)}
                          onChange={() => alternarAsignatura(a.id)}
                        />
                        <span>
                          {a.nombre} <small>{a.codigo} · {a.programa}</small>
                        </span>
                      </label>
                    </li>
                  ))}
                </ul>
              )}
              {mostrar('asignaturas') && <p className="campo-error">{errores.asignaturas}</p>}
            </fieldset>

            <fieldset>
              <legend className="tarjeta-subtitulo">
                Criterios de evaluación <small>(los pesos suman 100 %)</small>
              </legend>
              {criterios.map((c, indice) => (
                <div key={c.clave} className="criterio-fila">
                  <div className="campo">
                    <label htmlFor={`${id}-criterio-${c.clave}`}>Criterio {indice + 1}</label>
                    <input
                      id={`${id}-criterio-${c.clave}`}
                      type="text"
                      placeholder="Funcionalidad"
                      value={c.nombre}
                      onChange={(e) => cambiarCriterio(c.clave, 'nombre', e.target.value)}
                    />
                  </div>
                  <div className="campo">
                    <label htmlFor={`${id}-peso-${c.clave}`}>Peso (%)</label>
                    <input
                      id={`${id}-peso-${c.clave}`}
                      type="number"
                      min="1"
                      max="100"
                      step="any"
                      inputMode="decimal"
                      placeholder="50"
                      value={c.peso}
                      onChange={(e) => cambiarCriterio(c.clave, 'peso', e.target.value)}
                    />
                  </div>
                  {criterios.length > 1 ? (
                    <button
                      type="button"
                      className="boton-icono"
                      onClick={() => quitarCriterio(c.clave)}
                      aria-label={`Quitar el criterio ${indice + 1}`}
                    >
                      <Trash2 size={18} aria-hidden="true" />
                    </button>
                  ) : (
                    <span aria-hidden="true" />
                  )}
                </div>
              ))}
              <p className="campo-ayuda">Suma actual: {Number(sumaPesos.toFixed(2))} %</p>
              {mostrar('criterios') && <p className="campo-error">{errores.criterios}</p>}
              <button type="button" className="boton boton-secundario" onClick={agregarCriterio}>
                <Plus size={18} aria-hidden="true" /> Agregar criterio
              </button>
            </fieldset>

            <div className="acciones">
              <button type="submit" className="boton boton-azul" disabled={enviando}>
                <Plus size={18} aria-hidden="true" />
                {enviando ? 'Creando…' : 'Crear feria'}
              </button>
            </div>
          </form>

          {ferias.cargando ? (
            <Cargando texto="Cargando ferias…" />
          ) : ferias.error ? (
            <MensajeError error={ferias.error} alReintentar={ferias.recargar} />
          ) : feriasPropias.length === 0 ? (
            <div className="aviso aviso-info">
              <p>Esta institución todavía no tiene ferias.</p>
            </div>
          ) : (
            <div className="tabla-contenedor">
              <table className="tabla">
                <thead>
                  <tr>
                    <th scope="col">Feria</th>
                    <th scope="col">Inicio</th>
                    <th scope="col">Fin</th>
                    <th scope="col">Asignaturas participantes</th>
                  </tr>
                </thead>
                <tbody>
                  {feriasPropias.map((f) => (
                    <tr key={f.id}>
                      <td className="celda-principal">{f.nombre}</td>
                      <td>{formatearFecha(f.fecha_inicio)}</td>
                      <td>{formatearFecha(f.fecha_fin)}</td>
                      <td>{f.asignaturas.map((a) => a.nombre).join(', ') || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </section>
  )
}
