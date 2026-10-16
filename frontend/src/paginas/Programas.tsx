import { GraduationCap, Plus } from 'lucide-react'
import { useCallback, useId, useState, type SyntheticEvent } from 'react'
import { Link } from 'react-router-dom'
import type { ErrorApi } from '../api/cliente.ts'
import {
  listarDepartamentos,
  listarFacultades,
  listarProgramas,
  registrarPrograma,
} from '../api/endpoints.ts'
import type { Unidad } from '../api/tipos.ts'
import { Cargando, MensajeError } from '../componentes/Estados.tsx'
import { MenuEstructura, SelectorInstitucion } from '../componentes/MenuEstructura.tsx'
import { useConsulta } from '../hooks/useConsulta.ts'
import { useInstitucionElegida } from '../hooks/useInstitucionElegida.ts'
import { comoErrorApi } from '../utilidades.ts'

const cargarProgramas = () => listarProgramas()
const sinUnidades = () => Promise.resolve([] as Unidad[])

/**
 * HU-001 · REQ-3: programas académicos asociados a una facultad o a un departamento.
 * El código repetido o una facultad de otra institución los rechaza el backend.
 */
export function Programas() {
  const id = useId()
  const { instituciones, institucion, elegir } = useInstitucionElegida()
  const institucionId = institucion?.id ?? 0

  const cargarFacultades = useCallback(
    () => (institucionId ? listarFacultades(institucionId) : sinUnidades()),
    [institucionId],
  )
  const cargarDepartamentos = useCallback(
    () => (institucionId ? listarDepartamentos(institucionId) : sinUnidades()),
    [institucionId],
  )
  const facultades = useConsulta(cargarFacultades)
  const departamentos = useConsulta(cargarDepartamentos)
  const programas = useConsulta(cargarProgramas)

  const [codigo, setCodigo] = useState('')
  const [nombre, setNombre] = useState('')
  const [facultadId, setFacultadId] = useState('')
  const [departamentoId, setDepartamentoId] = useState('')
  const [intentado, setIntentado] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<ErrorApi | null>(null)
  const [exito, setExito] = useState('')

  const errores = {
    codigo: codigo.trim() ? '' : 'Escribe el código del programa.',
    nombre: nombre.trim() ? '' : 'Escribe el nombre del programa.',
    asociacion:
      facultadId || departamentoId ? '' : 'Elige la facultad o el departamento al que pertenece.',
  }
  const mostrar = (campo: keyof typeof errores) => intentado && errores[campo] !== ''

  const nombreDe = (lista: Unidad[] | null, buscado: number | null) =>
    lista?.find((u) => u.id === buscado)?.nombre
  const propios = programas.datos?.filter((p) => p.institucion_id === institucionId) ?? []

  function cambiarInstitucion(nueva: number) {
    elegir(nueva)
    setFacultadId('')
    setDepartamentoId('')
  }

  async function guardar(evento: SyntheticEvent<HTMLFormElement>) {
    evento.preventDefault()
    setIntentado(true)
    setError(null)
    setExito('')
    if (Object.values(errores).some(Boolean)) return
    setEnviando(true)
    try {
      const creado = await registrarPrograma({
        institucion_id: institucionId,
        codigo: codigo.trim(),
        nombre: nombre.trim(),
        facultad_id: facultadId ? Number(facultadId) : undefined,
        departamento_id: departamentoId ? Number(departamentoId) : undefined,
      })
      setExito(`El programa «${creado.nombre}» (${creado.codigo}) quedó registrado.`)
      setCodigo('')
      setNombre('')
      setFacultadId('')
      setDepartamentoId('')
      setIntentado(false)
      programas.recargar()
    } catch (causa) {
      setError(comoErrorApi(causa))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section className="pantalla pila">
      <div className="bienvenida">
        <h1>Programas académicos</h1>
        <p>Registra los programas y asócialos a una facultad o a un departamento.</p>
      </div>
      <MenuEstructura />

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
              <GraduationCap size={18} aria-hidden="true" /> Nuevo programa
            </h2>
            <div className="rejilla-2">
              <div className="campo">
                <label htmlFor={`${id}-codigo`}>Código</label>
                <input
                  id={`${id}-codigo`}
                  type="text"
                  placeholder="TDS"
                  value={codigo}
                  onChange={(e) => setCodigo(e.target.value)}
                  aria-invalid={mostrar('codigo')}
                />
                {mostrar('codigo') && <p className="campo-error">{errores.codigo}</p>}
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
              <div className="campo">
                <label htmlFor={`${id}-facultad`}>Facultad</label>
                <select
                  id={`${id}-facultad`}
                  value={facultadId}
                  onChange={(e) => setFacultadId(e.target.value)}
                >
                  <option value="">Sin facultad</option>
                  {facultades.datos?.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.nombre}
                    </option>
                  ))}
                </select>
              </div>
              <div className="campo">
                <label htmlFor={`${id}-departamento`}>Departamento</label>
                <select
                  id={`${id}-departamento`}
                  value={departamentoId}
                  onChange={(e) => setDepartamentoId(e.target.value)}
                >
                  <option value="">Sin departamento</option>
                  {departamentos.datos?.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.nombre}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            {mostrar('asociacion') && <p className="campo-error">{errores.asociacion}</p>}
            {facultades.datos?.length === 0 && departamentos.datos?.length === 0 && (
              <p className="campo-ayuda">
                Esta institución no tiene facultades ni departamentos.{' '}
                <Link to={`/estructura/facultades?institucion=${institucionId}`}>Agrégalos aquí</Link>.
              </p>
            )}

            <div className="acciones">
              <button type="submit" className="boton boton-azul" disabled={enviando}>
                <Plus size={18} aria-hidden="true" />
                {enviando ? 'Registrando…' : 'Registrar programa'}
              </button>
            </div>
          </form>

          {programas.cargando ? (
            <Cargando texto="Cargando programas…" />
          ) : programas.error ? (
            <MensajeError error={programas.error} alReintentar={programas.recargar} />
          ) : propios.length === 0 ? (
            <div className="aviso aviso-info">
              <p>Esta institución todavía no tiene programas.</p>
            </div>
          ) : (
            <div className="tabla-contenedor">
              <table className="tabla">
                <thead>
                  <tr>
                    <th scope="col">Código</th>
                    <th scope="col">Programa</th>
                    <th scope="col">Facultad</th>
                    <th scope="col">Departamento</th>
                  </tr>
                </thead>
                <tbody>
                  {propios.map((p) => (
                    <tr key={p.id}>
                      <td>
                        <span className="insignia insignia-azul">{p.codigo}</span>
                      </td>
                      <td className="celda-principal">{p.nombre}</td>
                      <td>{nombreDe(facultades.datos, p.facultad_id) ?? '—'}</td>
                      <td>{nombreDe(departamentos.datos, p.departamento_id) ?? '—'}</td>
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
