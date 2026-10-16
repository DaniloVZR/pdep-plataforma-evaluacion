import { ClipboardCheck, Eye } from 'lucide-react'
import { useCallback } from 'react'
import { Link } from 'react-router-dom'
import type { EvaluacionAsignada } from '../api/tipos.ts'
import { listarEvaluaciones } from '../api/endpoints.ts'
import { Cargando, MensajeError } from '../componentes/Estados.tsx'
import { useConsulta } from '../hooks/useConsulta.ts'
import { useSesion } from '../sesion/contexto.ts'
import { ETIQUETA_ESTADO } from '../utilidades.ts'

const CLASE_ESTADO = {
  PENDIENTE: 'insignia-gris',
  BORRADOR: 'insignia-naranja',
  CONFIRMADA: 'insignia-verde',
} as const

/** HU-007 · Paso 1: el evaluador ve los proyectos que tiene asignados (RNF-04). */
export function MisEvaluaciones() {
  const { sesion } = useSesion()
  const evaluadorId = sesion?.usuarioId ?? null

  const cargar = useCallback(
    () =>
      evaluadorId === null
        ? Promise.resolve([] as EvaluacionAsignada[])
        : listarEvaluaciones(evaluadorId),
    [evaluadorId],
  )
  const evaluaciones = useConsulta(cargar)

  const pendientes = evaluaciones.datos?.filter((e) => e.estado !== 'CONFIRMADA').length ?? 0

  return (
    <section className="pantalla">
      <div className="bienvenida">
        <h1>Mis evaluaciones</h1>
        <p>
          {evaluaciones.datos && evaluaciones.datos.length > 0
            ? `Tienes ${pendientes} ${pendientes === 1 ? 'proyecto por calificar' : 'proyectos por calificar'}.`
            : 'Proyectos que tienes asignados para calificar con la rúbrica de la feria.'}
        </p>
      </div>

      {evaluaciones.cargando ? (
        <Cargando texto="Cargando tus evaluaciones…" />
      ) : evaluaciones.error ? (
        <MensajeError error={evaluaciones.error} alReintentar={evaluaciones.recargar} />
      ) : evaluaciones.datos?.length === 0 ? (
        <div className="aviso aviso-info">
          <p>No tienes proyectos asignados por ahora.</p>
        </div>
      ) : (
        <div className="tabla-contenedor">
          <table className="tabla">
            <thead>
              <tr>
                <th scope="col">Proyecto</th>
                <th scope="col">Feria</th>
                <th scope="col">Estado</th>
                <th scope="col" className="numero">
                  Puntaje
                </th>
                <th scope="col">
                  <span className="solo-lectores">Acción</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {evaluaciones.datos?.map((e) => (
                <tr key={e.evaluacion_id}>
                  <td className="celda-principal">{e.proyecto}</td>
                  <td>{e.feria}</td>
                  <td>
                    <span className={`insignia ${CLASE_ESTADO[e.estado]}`}>
                      {ETIQUETA_ESTADO[e.estado]}
                    </span>
                  </td>
                  <td className="numero">
                    {e.puntaje_final === null ? '—' : e.puntaje_final.toFixed(2)}
                  </td>
                  <td className="celda-accion">
                    <Link
                      to={`/evaluaciones/${e.proyecto_id}`}
                      className={`boton ${e.estado === 'CONFIRMADA' ? 'boton-contorno' : 'boton-azul'}`}
                    >
                      {e.estado === 'CONFIRMADA' ? (
                        <>
                          <Eye size={16} aria-hidden="true" /> Ver
                        </>
                      ) : (
                        <>
                          <ClipboardCheck size={16} aria-hidden="true" /> Calificar
                        </>
                      )}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
