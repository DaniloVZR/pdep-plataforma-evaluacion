import { CheckCircle2, Clock } from 'lucide-react'
import { useCallback } from 'react'
import { Link } from 'react-router-dom'
import { consultarResultados } from '../api/endpoints.ts'
import type { ResultadoEvaluacion, ResultadoProyecto } from '../api/tipos.ts'
import { Cargando, MensajeError } from '../componentes/Estados.tsx'
import { useConsulta } from '../hooks/useConsulta.ts'
import { useSesion } from '../sesion/contexto.ts'
import { ETIQUETA_ESTADO, formatearFechaHora } from '../utilidades.ts'

const CLASE_ESTADO = {
  PENDIENTE: 'insignia-gris',
  BORRADOR: 'insignia-naranja',
  CONFIRMADA: 'insignia-verde',
} as const

/**
 * HU-009 · REQ-17: el estudiante consulta el puntaje final y la retroalimentación de cada
 * evaluador. El backend oculta ambos mientras la evaluación no esté confirmada (RN007).
 */
export function MisResultados() {
  const { sesion } = useSesion()
  const estudianteId = sesion?.usuarioId ?? null

  const cargar = useCallback(
    () =>
      estudianteId === null
        ? Promise.resolve([] as ResultadoProyecto[])
        : consultarResultados(estudianteId),
    [estudianteId],
  )
  const resultados = useConsulta(cargar)

  return (
    <section className="pantalla pila">
      <div className="bienvenida">
        <h1>Mis resultados</h1>
        <p>Calificación final y retroalimentación de los proyectos de tus equipos.</p>
      </div>

      {resultados.cargando ? (
        <Cargando texto="Cargando tus resultados…" />
      ) : resultados.error ? (
        <MensajeError error={resultados.error} alReintentar={resultados.recargar} />
      ) : resultados.datos?.length === 0 ? (
        <div className="aviso aviso-info">
          <p>
            Tus equipos todavía no tienen proyectos inscritos.{' '}
            <Link to="/proyectos/inscribir">Inscribe uno aquí</Link>.
          </p>
        </div>
      ) : (
        <ul className="lista-resultados">
          {resultados.datos?.map((proyecto) => (
            <li key={proyecto.proyecto_id} className="tarjeta">
              <h2 className="tarjeta-subtitulo">{proyecto.proyecto}</h2>
              <p className="texto-suave">
                {proyecto.feria} · {proyecto.equipo}
              </p>
              {proyecto.evaluaciones.length === 0 ? (
                <p className="estado">Este proyecto todavía no tiene evaluador asignado.</p>
              ) : (
                <ul className="lista-resultados">
                  {proyecto.evaluaciones.map((evaluacion) => (
                    <TarjetaEvaluacion key={evaluacion.evaluacion_id} evaluacion={evaluacion} />
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function TarjetaEvaluacion({ evaluacion }: { evaluacion: ResultadoEvaluacion }) {
  const confirmada = evaluacion.estado === 'CONFIRMADA'
  return (
    <li className="resultado-evaluacion">
      <div className="resultado-cabecera">
        <span className="fila-icono">
          {confirmada ? (
            <CheckCircle2 size={18} className="resultado-icono" aria-hidden="true" />
          ) : (
            <Clock size={18} aria-hidden="true" />
          )}
          Evaluador: <strong>{evaluacion.evaluador}</strong>
        </span>
        <span className={`insignia ${CLASE_ESTADO[evaluacion.estado]}`}>
          {ETIQUETA_ESTADO[evaluacion.estado]}
        </span>
      </div>

      {confirmada ? (
        <>
          <p className="resultado-puntaje">
            {evaluacion.puntaje_final === null ? '—' : evaluacion.puntaje_final.toFixed(2)}
            <small> / 5.0</small>
          </p>
          {evaluacion.fecha_confirmacion && (
            <p className="texto-suave">
              Confirmada el {formatearFechaHora(evaluacion.fecha_confirmacion)}
            </p>
          )}
          <blockquote className="retroalimentacion">
            <p className="tarjeta-subtitulo">Retroalimentación</p>
            <p>{evaluacion.retroalimentacion || 'El evaluador no dejó comentarios.'}</p>
          </blockquote>
        </>
      ) : (
        <p className="estado">
          La calificación y la retroalimentación se publican cuando el evaluador confirme la
          evaluación.
        </p>
      )}
    </li>
  )
}
