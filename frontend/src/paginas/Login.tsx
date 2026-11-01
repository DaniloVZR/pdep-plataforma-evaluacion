import { ArrowLeft, Eye, EyeOff, Lock, Mail } from 'lucide-react'
import { useId, useState, type SyntheticEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import type { ErrorApi } from '../api/cliente.ts'
import { iniciarSesion } from '../api/endpoints.ts'
import { MensajeError } from '../componentes/Estados.tsx'
import { Marca } from '../componentes/Marca.tsx'
import { RUTA_INICIAL, useSesion } from '../sesion/contexto.ts'
import { comoErrorApi } from '../utilidades.ts'

/** Inicio de sesión con roles (RNF-03): el servidor valida la cuenta y devuelve su rol. */
export function Login() {
  const { iniciar } = useSesion()
  const navegar = useNavigate()
  const idCorreo = useId()
  const idClave = useId()
  const [correo, setCorreo] = useState('')
  const [clave, setClave] = useState('')
  const [verClave, setVerClave] = useState(false)
  const [intentado, setIntentado] = useState(false)
  const [recuperar, setRecuperar] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [errorServidor, setErrorServidor] = useState<ErrorApi | null>(null)

  const errorCorreo = !correo.trim()
    ? 'Escribe tu correo institucional.'
    : !/^[^@\s]+@[^@\s]+$/.test(correo.trim())
      ? 'Escribe un correo válido, por ejemplo nombre@pascualbravo.edu.co.'
      : ''
  const errorClave = clave ? '' : 'Escribe tu contraseña.'

  async function ingresar(evento: SyntheticEvent<HTMLFormElement>) {
    evento.preventDefault()
    setIntentado(true)
    setErrorServidor(null)
    if (errorCorreo || errorClave) return

    setEnviando(true)
    try {
      const respuesta = await iniciarSesion({ correo: correo.trim(), clave })
      iniciar({
        cuenta: respuesta.nombre,
        rolCuenta: respuesta.rol,
        rol: respuesta.rol,
        usuarioId: respuesta.usuario_id,
        nombre: respuesta.nombre,
      })
      navegar(RUTA_INICIAL[respuesta.rol])
    } catch (causa) {
      setErrorServidor(comoErrorApi(causa))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="login">
      <div className="login-contenido">
        <form className="login-tarjeta" onSubmit={ingresar} noValidate>
          <div className="login-marca">
            <Marca />
          </div>
          <h1>Iniciar sesión</h1>

          <div className="campo">
            <label htmlFor={idCorreo}>Correo institucional</label>
            <div className="entrada">
              <Mail size={18} aria-hidden="true" />
              <input
                id={idCorreo}
                type="email"
                autoComplete="username"
                placeholder="nombre@pascualbravo.edu.co"
                value={correo}
                onChange={(e) => setCorreo(e.target.value)}
                aria-invalid={intentado && errorCorreo !== ''}
                aria-describedby={intentado && errorCorreo ? `${idCorreo}-error` : undefined}
              />
            </div>
            {intentado && errorCorreo && (
              <p className="campo-error" id={`${idCorreo}-error`} role="alert">
                {errorCorreo}
              </p>
            )}
          </div>

          <div className="campo">
            <label htmlFor={idClave}>Contraseña</label>
            <div className="entrada">
              <Lock size={18} aria-hidden="true" />
              <input
                id={idClave}
                type={verClave ? 'text' : 'password'}
                autoComplete="current-password"
                value={clave}
                onChange={(e) => setClave(e.target.value)}
                aria-invalid={intentado && errorClave !== ''}
                aria-describedby={intentado && errorClave ? `${idClave}-error` : undefined}
              />
              <button
                type="button"
                className="entrada-ojo"
                onClick={() => setVerClave((v) => !v)}
                aria-label={verClave ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                aria-pressed={verClave}
              >
                {verClave ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
              </button>
            </div>
            {intentado && errorClave && (
              <p className="campo-error" id={`${idClave}-error`} role="alert">
                {errorClave}
              </p>
            )}
            <button type="button" className="enlace-discreto" onClick={() => setRecuperar(true)}>
              ¿Olvidaste tu contraseña?
            </button>
            {recuperar && (
              <p className="campo-ayuda" role="status">
                Comunícate con el administrador de la plataforma para restablecer tu contraseña.
              </p>
            )}
          </div>

          {errorServidor && <MensajeError error={errorServidor} />}

          <button
            type="submit"
            className="boton boton-azul boton-ancho boton-grande"
            disabled={enviando}
          >
            {enviando ? 'Ingresando…' : 'Ingresar'}
          </button>

          <p className="login-pie">
            ¿No tienes cuenta? <Link to="/">Regístrate aquí</Link>
          </p>
        </form>

        <Link to="/" className="login-volver">
          <ArrowLeft size={16} aria-hidden="true" /> Volver al inicio
        </Link>
      </div>
    </div>
  )
}
