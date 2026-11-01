import { ArrowLeft, CheckCircle2, Save } from 'lucide-react'
import { useCallback, useId, useState, type SyntheticEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import type { ErrorApi } from '../api/cliente.ts'
import { calificarProyecto, listarEvaluaciones, obtenerRubrica } from '../api/endpoints.ts'
import type { Evaluacion, EvaluacionAsignada, Rubrica } from '../api/tipos.ts'
import { Cargando, MensajeError } from '../componentes/Estados.tsx'
import { useConsulta } from '../hooks/useConsulta.ts'
import { useSesion } from '../sesion/contexto.ts'
import { comoErrorApi, ETIQUETA_ESTADO, formatearFechaHora } from '../utilidades.ts'

/**
 * HU-007 · Paso 2: el evaluador califica cada criterio de la rúbrica.
 * El puntaje (Σ nota × peso) lo calcula el backend y solo se muestra al confirmar (RN006, RN007).
 */
export function CalificarProyecto() {
  const { proyectoId } = useParams()
  const { sesion } = useSesion()
  const evaluadorId = sesion?.usuarioId ?? null

  // La feria del proyecto sale de la lista de evaluaciones del evaluador.
  const cargarAsignadas = useCallback(
    () =>
      evaluadorId === null
        ? Promise.resolve([] as EvaluacionAsignada[])
        : listarEvaluaciones(evaluadorId),
    [evaluadorId],
  )
  const asignadas = useConsulta(cargarAsignadas)
  const asignada = asignadas.datos?.find((e) => String(e.proyecto_id) === proyectoId)
  const feriaId = asignada?.feria_id ?? null

  const cargarRubrica = useCallback(
    () => (feriaId === null ? Promise.resolve(null) : obtenerRubrica(feriaId)),
    [feriaId],
  )
  const rubrica = useConsulta(cargarRubrica)

  return (
    <section className="pantalla">
      <Link to="/evaluaciones" className="volver">
        <ArrowLeft size={16} aria-hidden="true" /> Mis evaluaciones
      </Link>

      {asignadas.cargando ? (
        <Cargando texto="Cargando la evaluación…" />
      ) : asignadas.error ? (
        <MensajeError error={asignadas.error} alReintentar={asignadas.recargar} />
      ) : !asignada || evaluadorId === null ? (
        <div className="aviso aviso-error" role="alert">
          <p>No tienes asignado este proyecto, así que no puedes calificarlo.</p>
        </div>
      ) : (
        <>
          <div className="bienvenida">
            <h1>{asignada.proyecto}</h1>
            <p>{asignada.feria}</p>
          </div>

          {rubrica.cargando ? (
            <Cargando texto="Cargando la rúbrica…" />
          ) : rubrica.error ? (
            // RN005: sin rúbrica asociada a la feria no se puede calificar.
            <MensajeError error={rubrica.error} alReintentar={rubrica.recargar} />
          ) : rubrica.datos ? (
            <FormularioRubrica
              rubrica={rubrica.datos}
              asignada={asignada}
              evaluadorId={evaluadorId}
            />
          ) : null}
        </>
      )}
    </section>
  )
}

interface PropsFormulario {
  rubrica: Rubrica
  asignada: EvaluacionAsignada
  evaluadorId: number
}

function FormularioRubrica({ rubrica, asignada, evaluadorId }: PropsFormulario) {
  const id = useId()
  const { nota_minima: minima, nota_maxima: maxima } = rubrica
  // Si había un borrador, el formulario arranca con las notas que ya se habían guardado.
  const [notas, setNotas] = useState<Record<number, string>>(() =>
    Object.fromEntries(
      Object.entries(asignada.notas ?? {}).map(([criterioId, nota]) => [criterioId, String(nota)]),
    ),
  )
  // HU-009: si había un borrador, se recupera el comentario que ya se había escrito.
  const [retroalimentacion, setRetroalimentacion] = useState(asignada.retroalimentacion ?? '')
  const [intentado, setIntentado] = useState(false)
  const [enviando, setEnviando] = useState<'borrador' | 'confirmar' | null>(null)
  const [errorServidor, setErrorServidor] = useState<ErrorApi | null>(null)
  const [borradorGuardado, setBorradorGuardado] = useState(false)
  const [huboBorrador, setHuboBorrador] = useState(false)
  const [resultado, setResultado] = useState<Evaluacion | null>(null)
  const estadoActual = huboBorrador ? 'BORRADOR' : asignada.estado

  const confirmada = asignada.estado === 'CONFIRMADA' || resultado?.estado === 'CONFIRMADA'

  function errorDe(criterioId: number): string {
    const texto = (notas[criterioId] ?? '').trim()
    if (texto === '') return 'Falta la nota.'
    const valor = Number(texto)
    if (Number.isNaN(valor)) return 'Debe ser un número.'
    if (valor < minima || valor > maxima) return `Debe estar entre ${minima} y ${maxima}.`
    return ''
  }
  const hayErrores = rubrica.criterios.some((c) => errorDe(c.id) !== '')

  async function enviar(confirmar: boolean) {
    setIntentado(true)
    setErrorServidor(null)
    setBorradorGuardado(false)
    if (hayErrores) return
    if (
      confirmar &&
      !window.confirm('Al confirmar se publica el puntaje y ya no podrás cambiar las notas. ¿Continuar?')
    ) {
      return
    }

    setEnviando(confirmar ? 'confirmar' : 'borrador')
    try {
      const respuesta = await calificarProyecto(asignada.proyecto_id, {
        evaluador_id: evaluadorId,
        notas: Object.fromEntries(rubrica.criterios.map((c) => [String(c.id), Number(notas[c.id])])),
        confirmar,
        retroalimentacion: retroalimentacion.trim(),
      })
      if (confirmar) setResultado(respuesta)
      else {
        setBorradorGuardado(true)
        setHuboBorrador(true)
      }
    } catch (causa) {
      setErrorServidor(comoErrorApi(causa))
    } finally {
      setEnviando(null)
    }
  }

  function alEnviar(evento: SyntheticEvent<HTMLFormElement>) {
    evento.preventDefault()
    void enviar(true)
  }

  // Ya confirmada: solo lectura con el puntaje y la constancia (RNF-06).
  if (confirmada) {
    const puntaje = resultado?.puntaje_final ?? asignada.puntaje_final
    const fecha = resultado?.fecha_confirmacion ?? asignada.fecha_confirmacion
    const conDesglose = resultado !== null
    const comentario = resultado?.retroalimentacion ?? asignada.retroalimentacion ?? ''
    return (
      <div className="tarjeta resultado">
        <CheckCircle2 size={40} className="resultado-icono" aria-hidden="true" />
        <p className="resultado-titulo">Evaluación confirmada</p>
        <p className="resultado-puntaje">
          {puntaje === null ? '—' : puntaje.toFixed(2)}
          <small> / {maxima}</small>
        </p>
        {fecha && <p className="texto-suave">Confirmada el {formatearFechaHora(fecha)}</p>}
        {comentario && (
          <blockquote className="retroalimentacion">
            <p className="tarjeta-subtitulo">Retroalimentación para el equipo</p>
            <p>{comentario}</p>
          </blockquote>
        )}

        {conDesglose && (
          <table className="tabla tabla-compacta">
            <caption className="texto-suave">Puntaje = Σ (nota × peso)</caption>
            <thead>
              <tr>
                <th scope="col">Criterio</th>
                <th scope="col" className="numero">Nota</th>
                <th scope="col" className="numero">Peso</th>
                <th scope="col" className="numero">Aporte</th>
              </tr>
            </thead>
            <tbody>
              {rubrica.criterios.map((c) => {
                const nota = Number(notas[c.id])
                return (
                  <tr key={c.id}>
                    <td>{c.nombre}</td>
                    <td className="numero">{nota.toFixed(1)}</td>
                    <td className="numero">{Math.round(c.peso * 100)} %</td>
                    <td className="numero">{(nota * c.peso).toFixed(2)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}

        <Link to="/evaluaciones" className="boton boton-azul">
          Volver a mis evaluaciones
        </Link>
      </div>
    )
  }

  return (
    <form className="tarjeta" onSubmit={alEnviar} noValidate>
      <p className="tarjeta-subtitulo">
        Rúbrica · escala de {minima} a {maxima}
        <span className="texto-suave"> · Estado: {ETIQUETA_ESTADO[estadoActual]}</span>
      </p>

      {errorServidor && <MensajeError error={errorServidor} />}
      {borradorGuardado && (
        <div className="aviso aviso-info" role="status">
          <p>Borrador guardado. El puntaje se calcula y se publica cuando confirmes.</p>
        </div>
      )}

      <ul className="criterios">
        {rubrica.criterios.map((c) => {
          const error = intentado ? errorDe(c.id) : ''
          return (
            <li key={c.id} className="criterio">
              <label htmlFor={`${id}-${c.id}`} className="criterio-nombre">
                {c.nombre}
                <span className="insignia insignia-azul">{Math.round(c.peso * 100)} %</span>
              </label>
              <div>
                <input
                  id={`${id}-${c.id}`}
                  type="number"
                  inputMode="decimal"
                  min={minima}
                  max={maxima}
                  step={0.1}
                  value={notas[c.id] ?? ''}
                  onChange={(e) => {
                    setNotas((actuales) => ({ ...actuales, [c.id]: e.target.value }))
                    setBorradorGuardado(false)
                  }}
                  aria-invalid={error !== ''}
                  className="criterio-nota"
                />
                {error && <p className="campo-error">{error}</p>}
              </div>
            </li>
          )
        })}
      </ul>

      <div className="campo">
        <label htmlFor={`${id}-retroalimentacion`}>
          Retroalimentación para el equipo <small className="texto-suave">(opcional)</small>
        </label>
        <textarea
          id={`${id}-retroalimentacion`}
          rows={4}
          value={retroalimentacion}
          onChange={(e) => {
            setRetroalimentacion(e.target.value)
            setBorradorGuardado(false)
          }}
        />
        <p className="campo-ayuda">El equipo la verá junto con el puntaje cuando confirmes (RN007).</p>
      </div>

      <div className="acciones">
        <button
          type="button"
          className="boton boton-contorno"
          disabled={enviando !== null}
          onClick={() => void enviar(false)}
        >
          <Save size={18} aria-hidden="true" />
          {enviando === 'borrador' ? 'Guardando…' : 'Guardar borrador'}
        </button>
        <button type="submit" className="boton boton-naranja" disabled={enviando !== null}>
          <CheckCircle2 size={18} aria-hidden="true" />
          {enviando === 'confirmar' ? 'Confirmando…' : 'Confirmar evaluación'}
        </button>
      </div>
    </form>
  )
}
