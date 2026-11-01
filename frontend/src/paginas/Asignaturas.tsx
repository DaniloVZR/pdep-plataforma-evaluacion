import { BookOpen, Plus } from 'lucide-react'
import { useCallback, useId, useState, type SyntheticEvent } from 'react'
import { Link } from 'react-router-dom'
import type { ErrorApi } from '../api/cliente.ts'
import { listarAsignaturas, listarProgramas, registrarAsignatura } from '../api/endpoints.ts'
import type { AsignaturaListada } from '../api/tipos.ts'
import { Cargando, MensajeError } from '../componentes/Estados.tsx'
import { MenuEstructura, SelectorInstitucion } from '../componentes/MenuEstructura.tsx'
import { useConsulta } from '../hooks/useConsulta.ts'
import { useInstitucionElegida } from '../hooks/useInstitucionElegida.ts'
import { comoErrorApi } from '../utilidades.ts'

const cargarProgramas = () => listarProgramas()
const sinAsignaturas = () => Promise.resolve([] as AsignaturaListada[])

/**
 * HU-002 · REQ-4: registrar asignaturas y asociarlas al programa académico seleccionado.
 * El programa inexistente (404) y el código repetido (409) los rechaza el backend.
 */
export function Asignaturas() {
  const id = useId()
  const { instituciones, institucion, elegir } = useInstitucionElegida()
  const institucionId = institucion?.id ?? 0
  const programas = useConsulta(cargarProgramas)
  const propios = programas.datos?.filter((p) => p.institucion_id === institucionId) ?? []

  // Criterio 1: se trabaja siempre sobre un programa elegido (por defecto, el primero).
  const [programaElegido, setProgramaElegido] = useState('')
  const programa = propios.find((p) => String(p.id) === programaElegido) ?? propios[0] ?? null
  const programaId = programa?.id ?? 0

  const cargarAsignaturas = useCallback(
    () => (programaId ? listarAsignaturas(programaId) : sinAsignaturas()),
    [programaId],
  )
  const asignaturas = useConsulta(cargarAsignaturas)

  const [codigo, setCodigo] = useState('')
  const [nombre, setNombre] = useState('')
  const [semestre, setSemestre] = useState('')
  const [intentado, setIntentado] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<ErrorApi | null>(null)
  const [exito, setExito] = useState('')

  const numeroSemestre = Number(semestre)
  const errores = {
    codigo: codigo.trim() ? '' : 'Escribe el código de la asignatura.',
    nombre: nombre.trim() ? '' : 'Escribe el nombre de la asignatura.',
    semestre:
      Number.isInteger(numeroSemestre) && numeroSemestre > 0
        ? ''
        : 'El semestre debe ser un número entero mayor que 0.',
  }
  const mostrar = (campo: keyof typeof errores) => intentado && errores[campo] !== ''

  function cambiarInstitucion(nueva: number) {
    elegir(nueva)
    setProgramaElegido('')
  }

  async function guardar(evento: SyntheticEvent<HTMLFormElement>) {
    evento.preventDefault()
    setIntentado(true)
    setError(null)
    setExito('')
    if (programa === null || Object.values(errores).some(Boolean)) return
    setEnviando(true)
    try {
      const creada = await registrarAsignatura({
        programa_id: programa.id,
        codigo: codigo.trim(),
        nombre: nombre.trim(),
        semestre: numeroSemestre,
      })
      setExito(`La asignatura «${creada.nombre}» (${creada.codigo}) quedó asociada a ${programa.nombre}.`)
      setCodigo('')
      setNombre('')
      setSemestre('')
      setIntentado(false)
      asignaturas.recargar()
    } catch (causa) {
      setError(comoErrorApi(causa))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section className="pantalla pila">
      <div className="bienvenida">
        <h1>Asignaturas</h1>
        <p>Registra las asignaturas y asócialas a un programa académico.</p>
      </div>
      <MenuEstructura />

      {instituciones.cargando || programas.cargando ? (
        <Cargando texto="Cargando programas…" />
      ) : instituciones.error ? (
        <MensajeError error={instituciones.error} alReintentar={instituciones.recargar} />
      ) : programas.error ? (
        <MensajeError error={programas.error} alReintentar={programas.recargar} />
      ) : institucion === null ? (
        <div className="aviso aviso-info">
          <p>
            Primero <Link to="/estructura/instituciones">registra una institución</Link>.
          </p>
        </div>
      ) : (
        <>
          <div className="rejilla-2">
            <SelectorInstitucion
              id={`${id}-institucion`}
              instituciones={instituciones.datos ?? []}
              elegida={institucion}
              alElegir={cambiarInstitucion}
            />
            {programa !== null && (
              <div className="campo filtro">
                <label htmlFor={`${id}-programa`}>Programa académico</label>
                <select
                  id={`${id}-programa`}
                  value={programa.id}
                  onChange={(e) => {
                    setProgramaElegido(e.target.value)
                    setExito('')
                    setError(null)
                  }}
                >
                  {propios.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.codigo} · {p.nombre}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {programa === null ? (
            <div className="aviso aviso-info">
              <p>
                Esta institución no tiene programas.{' '}
                <Link to={`/estructura/programas?institucion=${institucionId}`}>
                  Registra uno aquí
                </Link>
                .
              </p>
            </div>
          ) : (
            <>
              {exito && (
                <p className="aviso aviso-exito" role="status">
                  {exito}
                </p>
              )}
              {error && <MensajeError error={error} />}

              <form className="tarjeta" onSubmit={guardar} noValidate>
                <h2 className="tarjeta-subtitulo fila-icono">
                  <BookOpen size={18} aria-hidden="true" /> Nueva asignatura de {programa.nombre}
                </h2>
                <div className="rejilla-2">
                  <div className="campo">
                    <label htmlFor={`${id}-codigo`}>Código</label>
                    <input
                      id={`${id}-codigo`}
                      type="text"
                      placeholder="IS3"
                      value={codigo}
                      onChange={(e) => setCodigo(e.target.value)}
                      aria-invalid={mostrar('codigo')}
                    />
                    {mostrar('codigo') && <p className="campo-error">{errores.codigo}</p>}
                  </div>
                  <div className="campo">
                    <label htmlFor={`${id}-semestre`}>Semestre</label>
                    <input
                      id={`${id}-semestre`}
                      type="number"
                      inputMode="numeric"
                      min={1}
                      step={1}
                      value={semestre}
                      onChange={(e) => setSemestre(e.target.value)}
                      aria-invalid={mostrar('semestre')}
                    />
                    {mostrar('semestre') && <p className="campo-error">{errores.semestre}</p>}
                  </div>
                </div>
                <div className="campo">
                  <label htmlFor={`${id}-nombre`}>Nombre</label>
                  <input
                    id={`${id}-nombre`}
                    type="text"
                    value={nombre}
                    onChange={(e) => setNombre(e.target.value)}
                    aria-invalid={mostrar('nombre')}
                  />
                  {mostrar('nombre') && <p className="campo-error">{errores.nombre}</p>}
                </div>

                <div className="acciones">
                  <button type="submit" className="boton boton-azul" disabled={enviando}>
                    <Plus size={18} aria-hidden="true" />
                    {enviando ? 'Registrando…' : 'Registrar asignatura'}
                  </button>
                </div>
              </form>

              {asignaturas.cargando ? (
                <Cargando texto="Cargando asignaturas…" />
              ) : asignaturas.error ? (
                <MensajeError error={asignaturas.error} alReintentar={asignaturas.recargar} />
              ) : asignaturas.datos?.length === 0 ? (
                <div className="aviso aviso-info">
                  <p>Este programa todavía no tiene asignaturas.</p>
                </div>
              ) : (
                <div className="tabla-contenedor">
                  <table className="tabla">
                    <caption className="texto-suave">Asignaturas de {programa.nombre}</caption>
                    <thead>
                      <tr>
                        <th scope="col">Código</th>
                        <th scope="col">Asignatura</th>
                        <th scope="col" className="numero">
                          Semestre
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {asignaturas.datos?.map((a) => (
                        <tr key={a.id}>
                          <td>
                            <span className="insignia insignia-azul">{a.codigo}</span>
                          </td>
                          <td className="celda-principal">{a.nombre}</td>
                          <td className="numero">{a.semestre}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </>
      )}
    </section>
  )
}
