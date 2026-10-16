import { Plus } from 'lucide-react'
import { useCallback, useId, useState } from 'react'
import { Link } from 'react-router-dom'
import { listarFerias, listarProyectos } from '../api/endpoints.ts'
import { Cargando, MensajeError } from '../componentes/Estados.tsx'
import { useConsulta } from '../hooks/useConsulta.ts'
import { useSesion } from '../sesion/contexto.ts'
import { formatearFecha } from '../utilidades.ts'

const cargarFerias = () => listarFerias()

/** Proyectos inscritos, con filtro por feria. Lo ven los tres roles. */
export function ListadoProyectos() {
  const id = useId()
  const { sesion } = useSesion()
  const [feriaId, setFeriaId] = useState('')

  const ferias = useConsulta(cargarFerias)
  const cargarProyectos = useCallback(
    () => listarProyectos(feriaId ? Number(feriaId) : undefined),
    [feriaId],
  )
  const proyectos = useConsulta(cargarProyectos)
  const nombreFeria = (idFeria: number) => ferias.datos?.find((f) => f.id === idFeria)?.nombre ?? '—'

  return (
    <section className="pantalla">
      <div className="bienvenida bienvenida-con-accion">
        <div>
          <h1>Proyectos</h1>
          <p>Proyectos inscritos en las ferias de la institución.</p>
        </div>
        {sesion?.rol === 'ESTUDIANTE' && (
          <Link to="/proyectos/inscribir" className="boton boton-naranja">
            <Plus size={18} aria-hidden="true" /> Inscribir proyecto
          </Link>
        )}
      </div>

      <div className="campo filtro">
        <label htmlFor={`${id}-feria`}>Feria</label>
        <select id={`${id}-feria`} value={feriaId} onChange={(e) => setFeriaId(e.target.value)}>
          <option value="">Todas las ferias</option>
          {ferias.datos?.map((f) => (
            <option key={f.id} value={f.id}>
              {f.nombre}
            </option>
          ))}
        </select>
      </div>

      {proyectos.cargando ? (
        <Cargando texto="Cargando proyectos…" />
      ) : proyectos.error ? (
        <MensajeError error={proyectos.error} alReintentar={proyectos.recargar} />
      ) : proyectos.datos?.length === 0 ? (
        <div className="aviso aviso-info">
          <p>No hay proyectos inscritos {feriaId ? 'en esta feria' : 'todavía'}.</p>
        </div>
      ) : (
        <div className="tabla-contenedor">
          <table className="tabla">
            <thead>
              <tr>
                <th scope="col">Proyecto</th>
                <th scope="col">Equipo</th>
                <th scope="col">Feria</th>
                <th scope="col">Modalidad</th>
                <th scope="col">Inscrito</th>
              </tr>
            </thead>
            <tbody>
              {proyectos.datos?.map((p) => (
                <tr key={p.id}>
                  <td className="celda-principal">
                    {p.nombre}
                    {p.descripcion && <small className="celda-detalle">{p.descripcion}</small>}
                  </td>
                  <td>{p.equipo}</td>
                  <td>{nombreFeria(p.feria_id)}</td>
                  <td>
                    <span className="insignia insignia-azul">{p.modalidad}</span>
                  </td>
                  <td>{formatearFecha(p.fecha_inscripcion)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
