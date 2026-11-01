import { UserCheck } from 'lucide-react'
import { useId, useState, type SyntheticEvent } from 'react'
import type { ErrorApi } from '../api/cliente.ts'
import { asignarEvaluadores, listarCargaEvaluadores, listarProyectos } from '../api/endpoints.ts'
import { Cargando, MensajeError } from '../componentes/Estados.tsx'
import { useConsulta } from '../hooks/useConsulta.ts'
import { comoErrorApi } from '../utilidades.ts'

const cargarProyectos = () => listarProyectos()
const cargarCarga = () => listarCargaEvaluadores()

/**
 * HU-006 · El administrador asigna uno o varios docentes a un proyecto (REQ-11) y ve
 * cuántos proyectos tiene cada uno, para no sobrecargar a nadie. Los docentes que ya
 * tienen el proyecto salen desactivados; el backend igual rechaza la repetición (REQ-12).
 */
export function AsignarEvaluadores() {
  const id = useId()
  const proyectos = useConsulta(cargarProyectos)
  const carga = useConsulta(cargarCarga)

  const [proyectoId, setProyectoId] = useState('')
  const [elegidos, setElegidos] = useState<number[]>([])
  const [intentado, setIntentado] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [errorServidor, setErrorServidor] = useState<ErrorApi | null>(null)
  const [exito, setExito] = useState('')

  const proyecto = proyectos.datos?.find((p) => String(p.id) === proyectoId)
  const yaAsignados = new Set(proyecto?.evaluadores.map((e) => e.id) ?? [])
  const errores = {
    proyecto: proyectoId ? '' : 'Elige el proyecto.',
    evaluadores: elegidos.length > 0 ? '' : 'Elige al menos un evaluador.',
  }

  function alternar(evaluadorId: number) {
    setElegidos((actuales) =>
      actuales.includes(evaluadorId)
        ? actuales.filter((e) => e !== evaluadorId)
        : [...actuales, evaluadorId],
    )
  }

  async function guardar(evento: SyntheticEvent<HTMLFormElement>) {
    evento.preventDefault()
    setIntentado(true)
    setErrorServidor(null)
    setExito('')
    if (errores.proyecto || errores.evaluadores) return
    setEnviando(true)
    try {
      const respuesta = await asignarEvaluadores(Number(proyectoId), { evaluador_ids: elegidos })
      const cantidad = respuesta.asignados.length
      setExito(
        `${cantidad} ${cantidad === 1 ? 'evaluador asignado' : 'evaluadores asignados'} a «${proyecto?.nombre}».`,
      )
      setElegidos([])
      setIntentado(false)
      proyectos.recargar()
      carga.recargar()
    } catch (causa) {
      setErrorServidor(comoErrorApi(causa))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section className="pantalla pila">
      <div className="bienvenida">
        <h1>Asignar evaluadores</h1>
        <p>Asigna uno o varios docentes a cada proyecto y revisa la carga de cada evaluador.</p>
      </div>

      {exito && (
        <p className="aviso aviso-exito" role="status">
          {exito}
        </p>
      )}
      {errorServidor && <MensajeError error={errorServidor} />}

      <form className="tarjeta" onSubmit={guardar} noValidate>
        <div className="campo">
          <label htmlFor={`${id}-proyecto`}>Proyecto</label>
          {proyectos.cargando ? (
            <Cargando texto="Cargando proyectos…" />
          ) : proyectos.error ? (
            <MensajeError error={proyectos.error} alReintentar={proyectos.recargar} />
          ) : (
            <select
              id={`${id}-proyecto`}
              value={proyectoId}
              onChange={(e) => {
                setProyectoId(e.target.value)
                setElegidos([])
              }}
              aria-invalid={intentado && errores.proyecto !== ''}
            >
              <option value="">Selecciona un proyecto</option>
              {proyectos.datos?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre} · {p.equipo}
                </option>
              ))}
            </select>
          )}
          {intentado && errores.proyecto && <p className="campo-error">{errores.proyecto}</p>}
          {proyecto && (
            <p className="campo-ayuda">
              Evaluadores actuales:{' '}
              {proyecto.evaluadores.length
                ? proyecto.evaluadores.map((e) => e.nombres).join(', ')
                : 'ninguno todavía'}
            </p>
          )}
        </div>

        {proyecto && (
          <fieldset>
            <legend className="tarjeta-subtitulo">
              Docentes <small>(entre paréntesis, los proyectos que ya tiene cada uno)</small>
            </legend>
            {carga.cargando ? (
              <Cargando texto="Cargando docentes…" />
            ) : carga.error ? (
              <MensajeError error={carga.error} alReintentar={carga.recargar} />
            ) : carga.datos?.length === 0 ? (
              <p className="estado">No hay docentes registrados.</p>
            ) : (
              <ul className="opciones">
                {carga.datos?.map((d) => {
                  const asignado = yaAsignados.has(d.id)
                  return (
                    <li key={d.id}>
                      <label className="opcion">
                        <input
                          type="checkbox"
                          checked={asignado || elegidos.includes(d.id)}
                          disabled={asignado}
                          onChange={() => alternar(d.id)}
                        />
                        <span>
                          {d.nombres} ({d.asignados})
                          <small>{asignado ? 'Ya evalúa este proyecto' : d.correo}</small>
                        </span>
                      </label>
                    </li>
                  )
                })}
              </ul>
            )}
            {intentado && errores.evaluadores && (
              <p className="campo-error">{errores.evaluadores}</p>
            )}
          </fieldset>
        )}

        <div className="acciones">
          <button type="submit" className="boton boton-azul" disabled={enviando}>
            <UserCheck size={18} aria-hidden="true" />
            {enviando ? 'Asignando…' : 'Asignar evaluadores'}
          </button>
        </div>
      </form>

      <div>
        <h2 className="tarjeta-subtitulo">Carga por evaluador</h2>
        {carga.cargando ? (
          <Cargando />
        ) : carga.error ? (
          <MensajeError error={carga.error} alReintentar={carga.recargar} />
        ) : (
          <div className="tabla-contenedor">
            <table className="tabla">
              <thead>
                <tr>
                  <th scope="col">Evaluador</th>
                  <th scope="col" className="numero">Asignados</th>
                  <th scope="col" className="numero">Pendientes</th>
                  <th scope="col" className="numero">Borradores</th>
                  <th scope="col" className="numero">Confirmadas</th>
                </tr>
              </thead>
              <tbody>
                {carga.datos?.map((d) => (
                  <tr key={d.id}>
                    <td className="celda-principal">
                      {d.nombres}
                      <small className="celda-detalle">{d.correo}</small>
                    </td>
                    <td className="numero">
                      <strong>{d.asignados}</strong>
                    </td>
                    <td className="numero">{d.pendientes}</td>
                    <td className="numero">{d.borradores}</td>
                    <td className="numero">{d.confirmadas}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  )
}
