import { useCallback, useState, type SyntheticEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { listarUsuarios } from '../api/endpoints.ts'
import type { Rol } from '../api/tipos.ts'
import { Cargando, MensajeError } from '../componentes/Estados.tsx'
import { useConsulta } from '../hooks/useConsulta.ts'
import { ETIQUETA_ROL, RUTA_INICIAL, useSesion, type RolSesion } from '../sesion/contexto.ts'

interface OpcionRol {
  rol: RolSesion
  descripcion: string
  /** Rol de usuario del backend que se puede elegir; null si no hay que elegir a nadie. */
  usuarios: Rol | null
}

const OPCIONES: OpcionRol[] = [
  {
    rol: 'ADMINISTRADOR',
    descripcion: 'Registra estudiantes y docentes, y consulta los proyectos de cada feria.',
    usuarios: null,
  },
  {
    rol: 'EVALUADOR',
    descripcion: 'Califica con la rúbrica los proyectos que te asignaron.',
    usuarios: 'DOCENTE',
  },
  {
    rol: 'ESTUDIANTE',
    descripcion: 'Inscribe el proyecto de tu equipo en una feria abierta.',
    usuarios: 'ESTUDIANTE',
  },
]

export function Inicio() {
  const { iniciar } = useSesion()
  const navegar = useNavigate()
  const [rol, setRol] = useState<RolSesion | null>(null)
  const [usuarioId, setUsuarioId] = useState('')

  const opcion = OPCIONES.find((o) => o.rol === rol) ?? null
  const rolDeUsuarios = opcion?.usuarios ?? null

  const cargarUsuarios = useCallback(
    () => (rolDeUsuarios ? listarUsuarios(rolDeUsuarios) : Promise.resolve([])),
    [rolDeUsuarios],
  )
  const usuarios = useConsulta(cargarUsuarios)

  function elegirRol(nuevo: RolSesion) {
    setRol(nuevo)
    setUsuarioId('')
  }

  function entrar(evento: SyntheticEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (rol === null) return
    if (rol === 'ADMINISTRADOR') {
      iniciar({ rol, usuarioId: null, nombre: 'Administración' })
    } else {
      const elegido = usuarios.datos?.find((u) => String(u.id) === usuarioId)
      if (!elegido) return
      iniciar({ rol, usuarioId: elegido.id, nombre: elegido.nombres })
    }
    navegar(RUTA_INICIAL[rol])
  }

  const necesitaUsuario = rolDeUsuarios !== null
  const puedeEntrar = rol !== null && (!necesitaUsuario || usuarioId !== '')

  return (
    <section className="inicio">
      <div className="inicio-texto">
        <h1>Feria de proyectos, evaluada con una sola rúbrica</h1>
        <p className="lead">
          Inscribe proyectos, califica con criterios y pesos definidos, y consulta resultados sin
          hojas de cálculo ni correos de por medio.
        </p>
        <p className="nota">
          Esta es una sesión de demostración: el servidor aún no tiene inicio de sesión, así que
          eliges con qué rol entrar.
        </p>
      </div>

      <form className="inicio-formulario" onSubmit={entrar}>
        <fieldset>
          <legend>¿Con qué rol vas a entrar?</legend>
          {OPCIONES.map((o) => (
            <label key={o.rol} className={`opcion-rol${rol === o.rol ? ' opcion-rol-activa' : ''}`}>
              <input
                type="radio"
                name="rol"
                value={o.rol}
                checked={rol === o.rol}
                onChange={() => elegirRol(o.rol)}
              />
              <span className="opcion-rol-texto">
                <strong>{ETIQUETA_ROL[o.rol]}</strong>
                <span>{o.descripcion}</span>
              </span>
            </label>
          ))}
        </fieldset>

        {necesitaUsuario && (
          <div className="campo">
            <label htmlFor="usuario">
              {rol === 'EVALUADOR' ? '¿Qué docente eres?' : '¿Qué estudiante eres?'}
            </label>
            {usuarios.cargando ? (
              <Cargando texto="Cargando usuarios…" />
            ) : usuarios.error ? (
              <MensajeError error={usuarios.error} alReintentar={usuarios.recargar} />
            ) : usuarios.datos && usuarios.datos.length === 0 ? (
              <p className="estado">
                No hay usuarios con ese rol. Entra como administrador para registrar uno.
              </p>
            ) : (
              <select id="usuario" value={usuarioId} onChange={(e) => setUsuarioId(e.target.value)}>
                <option value="">Selecciona una persona</option>
                {usuarios.datos?.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.nombres} · {u.correo}
                  </option>
                ))}
              </select>
            )}
          </div>
        )}

        <button type="submit" className="boton boton-primario" disabled={!puedeEntrar}>
          Entrar
        </button>
      </form>
    </section>
  )
}
