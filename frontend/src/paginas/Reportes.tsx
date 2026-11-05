import { useCallback, useId, useState } from 'react'
import { generarReporte, listarFerias, listarProgramas } from '../api/endpoints.ts'
import type { Agrupacion, GrupoReporte } from '../api/tipos.ts'
import { Cargando, MensajeError } from '../componentes/Estados.tsx'
import { useConsulta } from '../hooks/useConsulta.ts'

const cargarFerias = () => listarFerias()
const cargarProgramas = () => listarProgramas()

const AGRUPACIONES: { valor: Agrupacion; texto: string }[] = [
  { valor: 'feria', texto: 'Por feria' },
  { valor: 'asignatura', texto: 'Por asignatura' },
  { valor: 'programa', texto: 'Por programa' },
]

const nota = (n: number) => n.toFixed(2)

/**
 * HU-010 · El administrador consolida los resultados (REQ-18) y los agrupa o filtra por
 * feria, asignatura o programa académico (REQ-19). El backend solo incluye los proyectos
 * con todas sus evaluaciones confirmadas y promedia los puntajes de sus evaluadores.
 */
export function Reportes() {
  const id = useId()
  const ferias = useConsulta(cargarFerias)
  const programas = useConsulta(cargarProgramas)

  const [agruparPor, setAgruparPor] = useState<Agrupacion>('feria')
  const [feriaId, setFeriaId] = useState('')
  const [programaId, setProgramaId] = useState('')
  const [asignaturaId, setAsignaturaId] = useState('')

  const cargar = useCallback(
    () =>
      generarReporte({
        agrupar_por: agruparPor,
        feria_id: Number(feriaId) || undefined,
        programa_id: Number(programaId) || undefined,
        asignatura_id: Number(asignaturaId) || undefined,
      }),
    [agruparPor, feriaId, programaId, asignaturaId],
  )
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

  const resumen = reporte.datos?.resumen
  const hayFiltros = feriaId !== '' || programaId !== '' || asignaturaId !== ''

  return (
    <section className="pantalla pila">
      <div className="bienvenida">
        <h1>Reportes de resultados</h1>
        <p>Puntajes consolidados de los proyectos con todas sus evaluaciones confirmadas.</p>
      </div>

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
        resumen && (
          <>
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
            </ul>

            {reporte.datos?.grupos.length === 0 ? (
              <div className="aviso aviso-info">
                <p>
                  Todavía no hay proyectos con todas sus evaluaciones confirmadas
                  {hayFiltros ? ' con estos filtros' : ''}.
                </p>
              </div>
            ) : (
              reporte.datos?.grupos.map((grupo) => (
                <TablaGrupo
                  key={grupo.id}
                  grupo={grupo}
                  mostrarFeria={reporte.datos?.agrupar_por !== 'feria'}
                />
              ))
            )}
          </>
        )
      )}
    </section>
  )
}

function TablaGrupo({ grupo, mostrarFeria }: { grupo: GrupoReporte; mostrarFeria: boolean }) {
  return (
    <article className="tarjeta grupo-reporte">
      <div className="grupo-cabecera">
        <h2 className="tarjeta-subtitulo">{grupo.nombre}</h2>
        <p className="texto-suave">
          {grupo.cantidad} {grupo.cantidad === 1 ? 'proyecto' : 'proyectos'} · promedio{' '}
          <strong>{nota(grupo.promedio)}</strong> · máximo {nota(grupo.maximo)} · mínimo{' '}
          {nota(grupo.minimo)}
        </p>
      </div>
      <div className="tabla-contenedor">
        <table className="tabla">
          <thead>
            <tr>
              <th scope="col" className="numero">
                #
              </th>
              <th scope="col">Proyecto</th>
              <th scope="col">Equipo</th>
              <th scope="col">Modalidad</th>
              {mostrarFeria && <th scope="col">Feria</th>}
              <th scope="col" className="numero">
                Evaluadores
              </th>
              <th scope="col" className="numero">
                Puntaje
              </th>
            </tr>
          </thead>
          <tbody>
            {grupo.proyectos.map((p, posicion) => (
              <tr key={p.proyecto_id}>
                <td className="numero">{posicion + 1}</td>
                <td className="celda-principal">{p.proyecto}</td>
                <td>{p.equipo}</td>
                <td>
                  <span className="insignia insignia-azul">{p.modalidad}</span>
                </td>
                {mostrarFeria && <td>{p.feria}</td>}
                <td className="numero">{p.evaluaciones}</td>
                <td className="numero">
                  <strong>{nota(p.puntaje)}</strong>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  )
}
