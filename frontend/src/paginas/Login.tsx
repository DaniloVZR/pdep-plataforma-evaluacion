import { ArrowLeft, Eye, EyeOff, Lock, Mail } from 'lucide-react'
import { useId, useState, type SyntheticEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Marca } from '../componentes/Marca.tsx'
import { RUTA_INICIAL, useSesion } from '../sesion/contexto.ts'

/** Por ahora todo ingreso entra como administrador: el servidor aún no autentica. */
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

  const errorCorreo = !correo.trim()
    ? 'Escribe tu correo institucional.'
    : !/^[^@\s]+@[^@\s]+$/.test(correo.trim())
      ? 'Escribe un correo válido, por ejemplo nombre@pascualbravo.edu.co.'
      : ''
  const errorClave = clave ? '' : 'Escribe tu contraseña.'

  function ingresar(evento: SyntheticEvent<HTMLFormElement>) {
    evento.preventDefault()
    setIntentado(true)
    if (errorCorreo || errorClave) return
    const cuenta = correo.trim().split('@')[0]
    iniciar({ cuenta, rol: 'ADMINISTRADOR', usuarioId: null, nombre: 'Administración' })
    navegar(RUTA_INICIAL.ADMINISTRADOR)
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
                La recuperación de contraseña estará disponible cuando el servidor tenga inicio de
                sesión.
              </p>
            )}
          </div>

          <button type="submit" className="boton boton-azul boton-ancho boton-grande">
            Ingresar
          </button>

          <p className="login-pie">
            ¿No tienes cuenta? <Link to="/">Regístrate aquí</Link>
          </p>
        </form>

        <p className="login-nota">
          Modo de demostración: cualquier correo y contraseña ingresan como administrador.
        </p>
        <Link to="/" className="login-volver">
          <ArrowLeft size={16} aria-hidden="true" /> Volver al inicio
        </Link>
      </div>
    </div>
  )
}
