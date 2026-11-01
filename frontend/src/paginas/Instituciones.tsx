import { Landmark, Plus } from 'lucide-react'
import { useId, useState, type SyntheticEvent } from 'react'
import type { ErrorApi } from '../api/cliente.ts'
import { registrarInstitucion } from '../api/endpoints.ts'
import { Cargando, MensajeError } from '../componentes/Estados.tsx'
import { MenuEstructura } from '../componentes/MenuEstructura.tsx'
import { useInstitucionElegida } from '../hooks/useInstitucionElegida.ts'
import { comoErrorApi } from '../utilidades.ts'

/**
 * HU-001 · REQ-1: el administrador registra instituciones con nombre, NIT y contacto.
 * Aquí solo se revisa que el nombre y el NIT estén llenos; el NIT o el dominio repetidos
 * los decide el backend y su mensaje se muestra tal cual.
 */
export function Instituciones() {
  const id = useId()
  const { instituciones, elegir } = useInstitucionElegida()

  const [nombre, setNombre] = useState('')
  const [nit, setNit] = useState('')
  const [correo, setCorreo] = useState('')
  const [telefono, setTelefono] = useState('')
  const [dominio, setDominio] = useState('')
  const [intentado, setIntentado] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<ErrorApi | null>(null)
  const [exito, setExito] = useState('')

  const errores = {
    nombre: nombre.trim() ? '' : 'Escribe el nombre de la institución.',
    nit: nit.trim() ? '' : 'Escribe el NIT de la institución.',
  }
  const mostrar = (campo: keyof typeof errores) => intentado && errores[campo] !== ''

  async function guardar(evento: SyntheticEvent<HTMLFormElement>) {
    evento.preventDefault()
    setIntentado(true)
    setError(null)
    setExito('')
    if (errores.nombre || errores.nit) return
    setEnviando(true)
    try {
      const creada = await registrarInstitucion({
        nombre: nombre.trim(),
        nit: nit.trim(),
        correo_contacto: correo.trim(),
        telefono: telefono.trim(),
        dominio: dominio.trim(),
      })
      setExito(`La institución «${creada.nombre}» quedó registrada.`)
      setNombre('')
      setNit('')
      setCorreo('')
      setTelefono('')
      setDominio('')
      setIntentado(false)
      instituciones.recargar()
      elegir(creada.id)
    } catch (causa) {
      setError(comoErrorApi(causa))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section className="pantalla pila">
      <div className="bienvenida">
        <h1>Instituciones</h1>
        <p>Registra la institución con su identificación y sus datos de contacto.</p>
      </div>
      <MenuEstructura />

      {exito && (
        <p className="aviso aviso-exito" role="status">
          {exito}
        </p>
      )}
      {error && <MensajeError error={error} />}

      <form className="tarjeta" onSubmit={guardar} noValidate>
        <h2 className="tarjeta-subtitulo fila-icono">
          <Landmark size={18} aria-hidden="true" /> Nueva institución
        </h2>
        <div className="rejilla-2">
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
            <label htmlFor={`${id}-nit`}>NIT (identificación)</label>
            <input
              id={`${id}-nit`}
              type="text"
              value={nit}
              onChange={(e) => setNit(e.target.value)}
              aria-invalid={mostrar('nit')}
            />
            {mostrar('nit') && <p className="campo-error">{errores.nit}</p>}
          </div>
          <div className="campo">
            <label htmlFor={`${id}-correo`}>
              Correo de contacto <small className="texto-suave">(opcional)</small>
            </label>
            <input
              id={`${id}-correo`}
              type="email"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
            />
          </div>
          <div className="campo">
            <label htmlFor={`${id}-telefono`}>
              Teléfono <small className="texto-suave">(opcional)</small>
            </label>
            <input
              id={`${id}-telefono`}
              type="text"
              inputMode="tel"
              value={telefono}
              onChange={(e) => setTelefono(e.target.value)}
            />
          </div>
          <div className="campo">
            <label htmlFor={`${id}-dominio`}>
              Dominio del correo institucional <small className="texto-suave">(opcional)</small>
            </label>
            <input
              id={`${id}-dominio`}
              type="text"
              placeholder="institucion.edu.co"
              value={dominio}
              onChange={(e) => setDominio(e.target.value)}
            />
            <p className="campo-ayuda">Con este dominio se validan los correos de sus usuarios (RN001).</p>
          </div>
        </div>

        <div className="acciones">
          <button type="submit" className="boton boton-azul" disabled={enviando}>
            <Plus size={18} aria-hidden="true" />
            {enviando ? 'Registrando…' : 'Registrar institución'}
          </button>
        </div>
      </form>

      {instituciones.cargando ? (
        <Cargando texto="Cargando instituciones…" />
      ) : instituciones.error ? (
        <MensajeError error={instituciones.error} alReintentar={instituciones.recargar} />
      ) : instituciones.datos?.length === 0 ? (
        <div className="aviso aviso-info">
          <p>Todavía no hay instituciones. Registra la primera con el formulario.</p>
        </div>
      ) : (
        <div className="tabla-contenedor">
          <table className="tabla">
            <thead>
              <tr>
                <th scope="col">Institución</th>
                <th scope="col">NIT</th>
                <th scope="col">Contacto</th>
                <th scope="col">Dominio</th>
              </tr>
            </thead>
            <tbody>
              {instituciones.datos?.map((i) => (
                <tr key={i.id}>
                  <td className="celda-principal">{i.nombre}</td>
                  <td>{i.nit}</td>
                  <td>{[i.correo_contacto, i.telefono].filter(Boolean).join(' · ') || '—'}</td>
                  <td>{i.dominios.join(', ') || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
