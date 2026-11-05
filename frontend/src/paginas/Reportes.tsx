import { ChevronDown, ChevronUp, FileSpreadsheet } from 'lucide-react'
import { Fragment, useCallback, useId, useMemo, useState } from 'react'
import type { ErrorApi } from '../api/cliente.ts'
import {
  descargarReporteExcel,
  generarReporte,
  listarFerias,
  listarProgramas,
} from '../api/endpoints.ts'
import type {
  Agrupacion,
  Distribucion,
  FiltrosReporte,
  GrupoReporte,
  NivelDesempeno,
  NotaCriterio,
  ProyectoConsolidado,
  Reporte,
} from '../api/tipos.ts'
import { Cargando, MensajeError } from '../componentes/Estados.tsx'
import { useConsulta } from '../hooks/useConsulta.ts'
import { comoErrorApi, ETIQUETA_ESTADO, formatearFechaHora } from '../utilidades.ts'

const cargarFerias = () => listarFerias()
const cargarProgramas = () => listarProgramas()

const AGRUPACIONES: { valor: Agrupacion; texto: string }[] = [
  { valor: 'feria', texto: 'Por feria' },
  { valor: 'asignatura', texto: 'Por asignatura' },
  { valor: 'programa', texto: 'Por programa' },
]

const NIVELES: { clave: keyof Distribucion; nivel: NivelDesempeno; texto: string; rango: string }[] = [
  { clave: 'excelente', nivel: 'EXCELENTE', texto: 'Excelente', rango: '4.5 – 5.0' },
  { clave: 'bueno', nivel: 'BUENO', texto: 'Bueno', rango: '4.0 – 4.4' },
  { clave: 'aceptable', nivel: 'ACEPTABLE', texto: 'Aceptable', rango: '3.0 – 3.9' },
  { clave: 'insuficiente', nivel: 'INSUFICIENTE', texto: 'Insuficiente', rango: 'menos de 3.0' },
]

const ETIQUETA_NIVEL: Record<NivelDesempeno, { texto: string; clase: string }> = {
  EXCELENTE: { texto: 'Excelente', clase: 'insignia-verde' },
  BUENO: { texto: 'Bueno', clase: 'insignia-azul' },
  ACEPTABLE: { texto: 'Aceptable', clase: 'insignia-naranja' },
  INSUFICIENTE: { texto: 'Insuficiente', clase: 'insignia-roja' },
}

/** Escala de las rúbricas (HU-004): las barras de los criterios se miden sobre 5. */
const NOTA_MAXIMA = 5

const nota = (n: number) => n.toFixed(2)
const porcentaje = (parte: number, total: number) => (total ? Math.round((parte * 100) / total) : 0)

/**
 * HU-010 · El administrador consolida los resultados (REQ-18) y los agrupa o filtra por
 * feria, asignatura o programa académico (REQ-19). El backend solo incluye los proyectos
 * con todas sus evaluaciones confirmadas y promedia los puntajes de sus evaluadores.
 * Además muestra la distribución de notas, el promedio por criterio, el avance de la
 * evaluación y el detalle de cada proyecto; todo se puede descargar en Excel.
 */
export function Reportes() {
  const id = useId()
  const ferias = useConsulta(cargarFerias)
  const programas = useConsulta(cargarProgramas)

  const [agruparPor, setAgruparPor] = useState<Agrupacion>('feria')
  const [feriaId, setFeriaId] = useState('')
  const [programaId, setProgramaId] = useState('')
  const [asignaturaId, setAsignaturaId] = useState('')
  const [descargando, setDescargando] = useState(false)
  const [errorDescarga, setErrorDescarga] = useState<ErrorApi | null>(null)

  const filtros = useMemo<FiltrosReporte>(
    () => ({
      agrupar_por: agruparPor,
      feria_id: Number(feriaId) || undefined,
      programa_id: Number(programaId) || undefined,
      asignatura_id: Number(asignaturaId) || undefined,
    }),
    [agruparPor, feriaId, programaId, asignaturaId],
  )
  const cargar = useCallback(() => generarReporte(filtros), [filtros])
  const reporte = useConsulta(cargar)

  // Las asignaturas del selector dependen del programa elegido; sin programa, todas.
  const asignaturas = (programas.datos ?? [])
    .filter((p) => !programaId || String(p.id) === programaId)
    .flatMap((p) => p.asignaturas)

  function limpiar() {
    setFeriaId('')
    setProgramaId('')
    setAsignaturaId('')
  }

  async function descargar() {
    setErrorDescarga(null)
    setDescargando(true)
    try {
      await descargarReporteExcel(filtros)
    } catch (causa) {
      setErrorDescarga(comoErrorApi(causa))
    } finally {
      setDescargando(false)
    }
  }

  const hayFiltros = feriaId !== '' || programaId !== '' || asignaturaId !== ''

  return (
    <section className="pantalla pila reporte">
      <div className="bienvenida-con-accion">
        <div className="bienvenida">
          <h1>Reportes de resultados</h1>
          <p>Puntajes consolidados de los proyectos con todas sus evaluaciones confirmadas.</p>
        </div>
        <button
          type="button"
          className="boton boton-naranja"
          onClick={descargar}
          disabled={descargando || reporte.cargando || reporte.error !== null}
        >
          <FileSpreadsheet size={18} aria-hidden="true" />
          {descargando ? 'Generando Excel…' : 'Descargar Excel'}
        </button>
      </div>
      {errorDescarga && <MensajeError error={errorDescarga} />}

      <div className="tarjeta pila">
        <fieldset>
          <legend className="tarjeta-subtitulo">Agrupar resultados</legend>
          <div className="selector-segmentado">
            {AGRUPACIONES.map(({ valor, texto }) => (
              <label key={valor} className={agruparPor === valor ? 'activo' : ''}>
                <input
                  type="radio"
                  name={`${id}-agrupar`}
                  checked={agruparPor === valor}
                  onChange={() => setAgruparPor(valor)}
                />
                {texto}
              </label>
            ))}
          </div>
        </fieldset>

        <div className="rejilla-3">
          <div className="campo">
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
          <div className="campo">
            <label htmlFor={`${id}-programa`}>Programa académico</label>
            <select
              id={`${id}-programa`}
              value={programaId}
              onChange={(e) => {
                setProgramaId(e.target.value)
                setAsignaturaId('')
              }}
            >
              <option value="">Todos los programas</option>
              {programas.datos?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor={`${id}-asignatura`}>Asignatura</label>
            <select
              id={`${id}-asignatura`}
              value={asignaturaId}
              onChange={(e) => setAsignaturaId(e.target.value)}
            >
              <option value="">Todas las asignaturas</option>
              {asignaturas.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.codigo} · {a.nombre}
                </option>
              ))}
            </select>
          </div>
        </div>
        {hayFiltros && (
          <div>
            <button type="button" className="boton boton-secundario" onClick={limpiar}>
              Quitar filtros
            </button>
          </div>
        )}
      </div>

      {reporte.cargando ? (
        <Cargando texto="Consolidando resultados…" />
      ) : reporte.error ? (
        <MensajeError error={reporte.error} alReintentar={reporte.recargar} />
      ) : (
        reporte.datos && <ContenidoReporte reporte={reporte.datos} hayFiltros={hayFiltros} />
      )}
    </section>
  )
}

function ContenidoReporte({ reporte, hayFiltros }: { reporte: Reporte; hayFiltros: boolean }) {
  const { resumen, avance } = reporte
  return (
    <>
      <p className="texto-suave">Generado el {formatearFechaHora(reporte.generado)}</p>
      <ul className="cifras" aria-label="Resumen del reporte">
        <li className="cifra">
          <span className="cifra-valor">{resumen.proyectos_consolidados}</span>
          <span className="cifra-texto">Proyectos con evaluación confirmada</span>
        </li>
        <li className="cifra">
          <span className="cifra-valor">{resumen.proyectos_pendientes}</span>
          <span className="cifra-texto">Proyectos pendientes (no entran al reporte)</span>
        </li>
        <li className="cifra">
          <span className="cifra-valor">
            {resumen.promedio_general === null ? '—' : nota(resumen.promedio_general)}
          </span>
          <span className="cifra-texto">Promedio general</span>
        </li>
        <li className="cifra">
          <span className="cifra-valor">{avance.porcentaje.toFixed(0)} %</span>
          <span className="cifra-texto">Evaluaciones confirmadas</span>
        </li>
      </ul>

      <div className="rejilla-reporte">
        <TarjetaDistribucion distribucion={reporte.distribucion} />
        <section className="tarjeta" aria-labelledby="titulo-avance">
          <h2 id="titulo-avance" className="tarjeta-subtitulo">
            Avance de la evaluación
          </h2>
          <div
            className="progreso"
            role="progressbar"
            aria-valuenow={avance.porcentaje}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Evaluaciones confirmadas"
          >
            <span style={{ width: `${avance.porcentaje}%` }} />
          </div>
          <p className="texto-suave">
            {avance.confirmadas} de {avance.total} evaluaciones confirmadas
          </p>
          <ul className="lista-datos">
            <li>
              <span>En borrador</span> <strong>{avance.borradores}</strong>
            </li>
            <li>
              <span>Sin empezar</span> <strong>{avance.sin_empezar}</strong>
            </li>
            <li>
              <span>Proyectos sin evaluador asignado</span>{' '}
              <strong>{avance.proyectos_sin_evaluador}</strong>
            </li>
          </ul>
        </section>
      </div>

      {reporte.pendientes.length > 0 && (
        <section className="tarjeta" aria-labelledby="titulo-pendientes">
          <h2 id="titulo-pendientes" className="tarjeta-subtitulo">
            Proyectos pendientes <small>(no entran al reporte hasta que se confirmen)</small>
          </h2>
          <div className="tabla-contenedor">
            <table className="tabla">
              <thead>
                <tr>
                  <th scope="col">Proyecto</th>
                  <th scope="col">Feria</th>
                  <th scope="col" className="numero">
                    Confirmadas
                  </th>
                  <th scope="col">Falta</th>
                </tr>
              </thead>
              <tbody>
                {reporte.pendientes.map((p) => (
                  <tr key={p.proyecto_id}>
                    <td>
                      <span className="celda-principal">{p.proyecto}</span>
                      <span className="celda-detalle">{p.equipo}</span>
                    </td>
                    <td>{p.feria}</td>
                    <td className="numero">
                      {p.confirmadas} de {p.total}
                    </td>
                    <td>
                      {p.faltantes.length === 0 ? (
                        <span className="insignia insignia-roja">Sin evaluador asignado</span>
                      ) : (
                        <ul className="lista-simple lista-compacta">
                          {p.faltantes.map((f) => (
                            <li key={f.evaluador}>
                              {f.evaluador}{' '}
                              <span
                                className={`insignia ${f.estado === 'BORRADOR' ? 'insignia-naranja' : 'insignia-gris'}`}
                              >
                                {f.estado === 'PENDIENTE' ? 'Sin empezar' : ETIQUETA_ESTADO[f.estado]}
                              </span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {reporte.grupos.length === 0 ? (
        <div className="aviso aviso-info">
          <p>
            Todavía no hay proyectos con todas sus evaluaciones confirmadas
            {hayFiltros ? ' con estos filtros' : ''}.
          </p>
        </div>
      ) : (
        reporte.grupos.map((grupo) => (
          <TarjetaGrupo key={grupo.id} grupo={grupo} mostrarFeria={reporte.agrupar_por !== 'feria'} />
        ))
      )}
    </>
  )
}

/** Barras horizontales: cuántos proyectos hay en cada nivel de desempeño. */
function TarjetaDistribucion({ distribucion }: { distribucion: Distribucion }) {
  const total = distribucion.aprobados + distribucion.reprobados
  return (
    <section className="tarjeta" aria-labelledby="titulo-distribucion">
      <h2 id="titulo-distribucion" className="tarjeta-subtitulo">
        Distribución de notas
      </h2>
      <ul className="barras barras-apiladas">
        {NIVELES.map(({ clave, texto, rango }) => {
          const cantidad = distribucion[clave]
          return (
            <li key={clave} className="barra-fila" title={`${texto} (${rango}): ${cantidad}`}>
              <span className="barra-etiqueta">
                {texto} <small>{rango}</small>
              </span>
              <span className="barra-pista">
                <span className="barra" style={{ width: `${porcentaje(cantidad, total)}%` }} />
              </span>
              <span className="barra-valor">
                {cantidad} <small>({porcentaje(cantidad, total)} %)</small>
              </span>
            </li>
          )
        })}
      </ul>
      <p className="texto-suave">
        Aprobados (3.0 o más): <strong>{distribucion.aprobados}</strong> · Reprobados:{' '}
        <strong>{distribucion.reprobados}</strong>
      </p>
    </section>
  )
}

/** Promedio de cada criterio, medido sobre la nota máxima de la escala. */
function BarrasCriterios({ criterios }: { criterios: NotaCriterio[] }) {
  return (
    <ul className="barras">
      {criterios.map((c) => (
        <li key={c.criterio} className="barra-fila" title={`${c.criterio}: ${nota(c.nota)}`}>
          <span className="barra-etiqueta">
            {c.criterio} <small>{Math.round(c.peso * 100)} %</small>
          </span>
          <span className="barra-pista">
            <span className="barra" style={{ width: `${(c.nota / NOTA_MAXIMA) * 100}%` }} />
          </span>
          <span className="barra-valor">{nota(c.nota)}</span>
        </li>
      ))}
    </ul>
  )
}

function TarjetaGrupo({ grupo, mostrarFeria }: { grupo: GrupoReporte; mostrarFeria: boolean }) {
  const [abiertos, setAbiertos] = useState<number[]>([])
  const columnas = mostrarFeria ? 8 : 7

  function alternar(proyectoId: number) {
    setAbiertos((actuales) =>
      actuales.includes(proyectoId)
        ? actuales.filter((p) => p !== proyectoId)
        : [...actuales, proyectoId],
    )
  }

  return (
    <article className="tarjeta grupo-reporte">
      <div className="grupo-cabecera">
        <h2 className="tarjeta-subtitulo">{grupo.nombre}</h2>
        <p className="texto-suave">
          {grupo.cantidad} {grupo.cantidad === 1 ? 'proyecto' : 'proyectos'} · promedio{' '}
          <strong>{nota(grupo.promedio)}</strong> · máximo {nota(grupo.maximo)} · mínimo{' '}
          {nota(grupo.minimo)} · aprobados {grupo.distribucion.aprobados} de {grupo.cantidad}
        </p>
      </div>

      {grupo.criterios.length > 0 && (
        <div className="grupo-criterios">
          <h3 className="texto-suave">Promedio por criterio</h3>
          <BarrasCriterios criterios={grupo.criterios} />
        </div>
      )}

      <div className="tabla-contenedor">
        <table className="tabla">
          <thead>
            <tr>
              <th scope="col" className="numero">
                #
              </th>
              <th scope="col">Proyecto</th>
              <th scope="col" className="col-opcional">
                Modalidad
              </th>
              {mostrarFeria && (
                <th scope="col" className="col-opcional">
                  Feria
                </th>
              )}
              <th scope="col" className="numero col-opcional">
                Evaluadores
              </th>
              <th scope="col" className="numero">
                Puntaje
              </th>
              <th scope="col">Nivel</th>
              <th scope="col">
                <span className="solo-lectores">Detalle</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {grupo.proyectos.map((p, posicion) => {
              const abierto = abiertos.includes(p.proyecto_id)
              return (
                <Fragment key={p.proyecto_id}>
                  <tr>
                    <td className="numero">{posicion + 1}</td>
                    <td>
                      <span className="celda-principal">{p.proyecto}</span>
                      <span className="celda-detalle">{p.equipo}</span>
                    </td>
                    <td className="col-opcional">
                      <span className="insignia insignia-azul">{p.modalidad}</span>
                    </td>
                    {mostrarFeria && <td className="col-opcional">{p.feria}</td>}
                    <td className="numero col-opcional">{p.evaluaciones.length}</td>
                    <td className="numero">
                      <strong>{nota(p.puntaje)}</strong>
                    </td>
                    <td>
                      <span className={`insignia ${ETIQUETA_NIVEL[p.nivel].clase}`}>
                        {ETIQUETA_NIVEL[p.nivel].texto}
                      </span>
                    </td>
                    <td className="celda-accion">
                      <button
                        type="button"
                        className="boton boton-secundario"
                        aria-expanded={abierto}
                        onClick={() => alternar(p.proyecto_id)}
                      >
                        {abierto ? (
                          <ChevronUp size={16} aria-hidden="true" />
                        ) : (
                          <ChevronDown size={16} aria-hidden="true" />
                        )}
                        <span className="solo-escritorio">{abierto ? 'Ocultar' : 'Ver detalle'}</span>
                        <span className="solo-lectores solo-celular">
                          {abierto ? 'Ocultar detalle' : 'Ver detalle'}
                        </span>
                      </button>
                    </td>
                  </tr>
                  {abierto && (
                    <tr className="fila-detalle">
                      <td colSpan={columnas}>
                        <DetalleProyecto proyecto={p} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      </div>
    </article>
  )
}

function DetalleProyecto({ proyecto }: { proyecto: ProyectoConsolidado }) {
  return (
    <div className="detalle-proyecto">
      <dl className="datos-proyecto">
        <div>
          <dt>Integrantes</dt>
          <dd>{proyecto.integrantes.join(', ') || '—'}</dd>
        </div>
        <div>
          <dt>Asignaturas</dt>
          <dd>{proyecto.asignaturas.join(', ')}</dd>
        </div>
      </dl>
      {proyecto.criterios.length > 0 && (
        <div>
          <h4 className="texto-suave">Notas por criterio (promedio de los evaluadores)</h4>
          <BarrasCriterios criterios={proyecto.criterios} />
        </div>
      )}
      <div>
        <h4 className="texto-suave">Retroalimentación</h4>
        <ul className="lista-simple">
          {proyecto.evaluaciones.map((e) => (
            <li key={e.evaluador}>
              <strong>{e.evaluador}</strong> · {e.puntaje_final === null ? '—' : nota(e.puntaje_final)}
              {e.fecha_confirmacion && (
                <span className="texto-suave"> · {formatearFechaHora(e.fecha_confirmacion)}</span>
              )}
              <p>{e.retroalimentacion || 'Sin comentarios.'}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
