import { Building2, Network, Plus } from 'lucide-react'
import { useCallback, useId, useState, type ReactNode, type SyntheticEvent } from 'react'
import { Link } from 'react-router-dom'
import type { ErrorApi } from '../api/cliente.ts'
import {
  listarDepartamentos,
  listarFacultades,
  registrarDepartamento,
  registrarFacultad,
} from '../api/endpoints.ts'
import type { SolicitudUnidad, Unidad } from '../api/tipos.ts'
import { Cargando, MensajeError } from '../componentes/Estados.tsx'
import { MenuEstructura, SelectorInstitucion } from '../componentes/MenuEstructura.tsx'
import { useConsulta } from '../hooks/useConsulta.ts'
import { useInstitucionElegida } from '../hooks/useInstitucionElegida.ts'
import { comoErrorApi } from '../utilidades.ts'

const sinUnidades = () => Promise.resolve([] as Unidad[])

/** HU-001 · REQ-2: facultades y departamentos de una institución. */
export function FacultadesDepartamentos() {
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

  return (
    <section className="pantalla pila">
      <div className="bienvenida">
        <h1>Facultades y departamentos</h1>
        <p>Registra las facultades y los departamentos de la institución.</p>
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
            alElegir={elegir}
          />
          <div className="rejilla-2 rejilla-tarjetas">
            <FormularioUnidad
              titulo="Facultades"
              singular="facultad"
              icono={<Building2 size={18} aria-hidden="true" />}
              institucionId={institucion.id}
              consulta={facultades}
              registrar={registrarFacultad}
            />
            <FormularioUnidad
              titulo="Departamentos"
              singular="departamento"
              icono={<Network size={18} aria-hidden="true" />}
              institucionId={institucion.id}
              consulta={departamentos}
              registrar={registrarDepartamento}
            />
          </div>
        </>
      )}
    </section>
  )
}

interface PropsUnidad {
  titulo: string
  singular: 'facultad' | 'departamento'
  icono: ReactNode
  institucionId: number
  consulta: ReturnType<typeof useConsulta<Unidad[]>>
  registrar: (datos: SolicitudUnidad) => Promise<Unidad>
}

function FormularioUnidad({ titulo, singular, icono, institucionId, consulta, registrar }: PropsUnidad) {
  const id = useId()
  const [nombre, setNombre] = useState('')
  const [intentado, setIntentado] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<ErrorApi | null>(null)

  const de = singular === 'facultad' ? 'de la' : 'del'
  const errorNombre = nombre.trim() ? '' : `Escribe el nombre ${de} ${singular}.`

  async function guardar(evento: SyntheticEvent<HTMLFormElement>) {
    evento.preventDefault()
    setIntentado(true)
    setError(null)
    if (errorNombre) return
    setEnviando(true)
    try {
      await registrar({ institucion_id: institucionId, nombre: nombre.trim() })
      setNombre('')
      setIntentado(false)
      // Criterio de aceptación: la nueva aparece en el listado (menos de 2 s).
      consulta.recargar()
    } catch (causa) {
      setError(comoErrorApi(causa))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form className="tarjeta" onSubmit={guardar} noValidate>
      <h2 className="tarjeta-subtitulo fila-icono">
        {icono} {titulo}
      </h2>
      {error && <MensajeError error={error} />}
      <div className="campo">
        <label htmlFor={`${id}-nombre`}>
          Nombre {de} {singular}
        </label>
        <input
          id={`${id}-nombre`}
          type="text"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          aria-invalid={intentado && errorNombre !== ''}
        />
        {intentado && errorNombre && <p className="campo-error">{errorNombre}</p>}
      </div>
      <button type="submit" className="boton boton-azul" disabled={enviando}>
        <Plus size={18} aria-hidden="true" />
        {enviando ? 'Agregando…' : `Agregar ${singular}`}
      </button>

      {consulta.cargando ? (
        <Cargando />
      ) : consulta.error ? (
        <MensajeError error={consulta.error} alReintentar={consulta.recargar} />
      ) : consulta.datos?.length === 0 ? (
        <p className="estado">Sin {titulo.toLowerCase()} registrados.</p>
      ) : (
        <ul className="lista-simple">
          {consulta.datos?.map((u) => (
            <li key={u.id}>{u.nombre}</li>
          ))}
        </ul>
      )}
    </form>
  )
}
