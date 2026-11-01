import { ChevronDown, Eye } from 'lucide-react'
import { useCallback, useEffect, useId, useRef, useState, type SyntheticEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { listarUsuarios } from '../api/endpoints.ts'
import type { Rol, UsuarioResumen } from '../api/tipos.ts'
import { useConsulta } from '../hooks/useConsulta.ts'
import { ETIQUETA_ROL, RUTA_INICIAL, useSesion, type RolSesion } from '../sesion/contexto.ts'
import { Cargando, MensajeError } from './Estados.tsx'

const ROLES: RolSesion[] = ['ADMINISTRADOR', 'EVALUADOR', 'ESTUDIANTE']
const ROL_DE_USUARIOS: Record<RolSesion, Rol | null> = {
  ADMINISTRADOR: null,
  EVALUADOR: 'DOCENTE',
  ESTUDIANTE: 'ESTUDIANTE',
}

/**
 * Herramienta de demostración del administrador: muestra la plataforma como la
 * vería otro rol sin cerrar sesión. El layout solo la muestra a cuentas de administrador.
 */
export function CambiarVista() {
  const { sesion, iniciar } = useSesion()
  const navegar = useNavigate()
  const idPanel = useId()
  const contenedor = useRef<HTMLDivElement>(null)
  const [abierto, setAbierto] = useState(false)
  const [rol, setRol] = useState<RolSesion>(sesion?.rol ?? 'ADMINISTRADOR')
  const [usuarioId, setUsuarioId] = useState('')

  const rolDeUsuarios = ROL_DE_USUARIOS[rol]
  const cargar = useCallback(
    () =>
      abierto && rolDeUsuarios
        ? listarUsuarios(rolDeUsuarios)
        : Promise.resolve([] as UsuarioResumen[]),
    [abierto, rolDeUsuarios],
  )
  const usuarios = useConsulta(cargar)

  useEffect(() => {
    if (!abierto) return
    const alPulsar = (e: KeyboardEvent) => e.key === 'Escape' && setAbierto(false)
    const alHacerClic = (e: MouseEvent) => {
      if (!contenedor.current?.contains(e.target as Node)) setAbierto(false)
    }
    document.addEventListener('keydown', alPulsar)
    document.addEventListener('mousedown', alHacerClic)
    return () => {
      document.removeEventListener('keydown', alPulsar)
      document.removeEventListener('mousedown', alHacerClic)
    }
  }, [abierto])

  if (sesion === null) return null

  function aplicar(evento: SyntheticEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (sesion === null) return
    if (rol === 'ADMINISTRADOR') {
      iniciar({ ...sesion, rol, usuarioId: null, nombre: 'Administración' })
    } else {
      const elegido = usuarios.datos?.find((u) => String(u.id) === usuarioId)
      if (!elegido) return
      iniciar({ ...sesion, rol, usuarioId: elegido.id, nombre: elegido.nombres })
    }
    setAbierto(false)
    navegar(RUTA_INICIAL[rol])
  }

  const puedeAplicar = rolDeUsuarios === null || usuarioId !== ''

  return (
    <div className="vista" ref={contenedor}>
      <button
        type="button"
        className="boton boton-encabezado"
        aria-expanded={abierto}
        aria-controls={idPanel}
        onClick={() => setAbierto((v) => !v)}
      >
        <Eye size={16} aria-hidden="true" />
        Ver como
        <ChevronDown size={16} aria-hidden="true" />
      </button>

      {abierto && (
        <form id={idPanel} className="vista-panel" onSubmit={aplicar}>
          <p className="vista-titulo">Previsualizar otra vista</p>
          <p className="vista-ayuda">
            Muestra la plataforma como la vería otra persona, sin cerrar tu sesión de administrador.
          </p>

          <fieldset>
            <legend className="solo-lectores">Rol a previsualizar</legend>
            {ROLES.map((r) => (
              <label key={r} className="vista-opcion">
                <input
                  type="radio"
                  name="vista-rol"
                  checked={rol === r}
                  onChange={() => {
                    setRol(r)
                    setUsuarioId('')
                  }}
                />
                {ETIQUETA_ROL[r]}
              </label>
            ))}
          </fieldset>

          {rolDeUsuarios && (
            <div className="campo">
              <label htmlFor={`${idPanel}-usuario`}>
                {rol === 'EVALUADOR' ? 'Docente' : 'Estudiante'}
              </label>
              {usuarios.cargando ? (
                <Cargando texto="Cargando usuarios…" />
              ) : usuarios.error ? (
                <MensajeError error={usuarios.error} alReintentar={usuarios.recargar} />
              ) : usuarios.datos?.length === 0 ? (
                <p className="estado">No hay usuarios con ese rol.</p>
              ) : (
                <select
                  id={`${idPanel}-usuario`}
                  value={usuarioId}
                  onChange={(e) => setUsuarioId(e.target.value)}
                >
                  <option value="">Selecciona una persona</option>
                  {usuarios.datos?.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.nombres}
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}

          <button type="submit" className="boton boton-azul boton-ancho" disabled={!puedeAplicar}>
            Ver esta vista
          </button>
        </form>
      )}
    </div>
  )
}
