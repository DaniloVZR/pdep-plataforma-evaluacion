import { LogOut } from 'lucide-react'
import { NavLink, Navigate, Outlet, useNavigate } from 'react-router-dom'
import { ETIQUETA_ROL, RUTA_INICIAL, useSesion, type RolSesion } from '../sesion/contexto.ts'
import { CambiarVista } from './CambiarVista.tsx'
import { Marca } from './Marca.tsx'

// `seccion: true` deja el enlace marcado también en sus subpáginas (estructura académica).
const MENU: Record<RolSesion, { a: string; texto: string; seccion?: boolean }[]> = {
  ADMINISTRADOR: [
    { a: '/admin', texto: 'Panel' },
    { a: '/estructura', texto: 'Estructura académica', seccion: true },
    { a: '/ferias', texto: 'Ferias' },
    { a: '/usuarios/nuevo', texto: 'Registrar usuario' },
    { a: '/asignaciones', texto: 'Asignar evaluadores' },
    { a: '/proyectos', texto: 'Proyectos' },
  ],
  EVALUADOR: [
    { a: '/evaluaciones', texto: 'Mis evaluaciones' },
    { a: '/proyectos', texto: 'Proyectos' },
  ],
  ESTUDIANTE: [
    { a: '/proyectos/inscribir', texto: 'Inscribir proyecto' },
    { a: '/resultados', texto: 'Mis resultados' },
    { a: '/proyectos', texto: 'Proyectos' },
  ],
}

/** Estructura de las pantallas con sesión: encabezado azul, menú del rol y perfil. */
export function LayoutApp() {
  const { sesion, cerrar } = useSesion()
  const navegar = useNavigate()

  if (sesion === null) return <Navigate to="/ingresar" replace />

  function salir() {
    cerrar()
    navegar('/')
  }

  return (
    <div className="pagina pagina-app">
      <header className="encabezado encabezado-azul">
        <div className="encabezado-contenido">
          <Marca a={RUTA_INICIAL[sesion.rol]} />
          <nav className="menu" aria-label="Principal">
            {MENU[sesion.rol].map((enlace) => (
              <NavLink key={enlace.a} to={enlace.a} end={!enlace.seccion} className="menu-enlace">
                {enlace.texto}
              </NavLink>
            ))}
          </nav>
          <div className="encabezado-acciones">
            {sesion.rolCuenta === 'ADMINISTRADOR' && <CambiarVista />}
            <div className="perfil">
              <span className="perfil-texto">Bienvenido, {sesion.cuenta}</span>
              <span className="avatar" aria-hidden="true">
                {sesion.cuenta.charAt(0).toUpperCase()}
              </span>
              <button type="button" className="boton-icono" onClick={salir} aria-label="Cerrar sesión">
                <LogOut size={18} aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
        {sesion.rolCuenta === 'ADMINISTRADOR' && sesion.rol !== 'ADMINISTRADOR' && (
          <p className="franja-vista" role="status">
            Estás viendo la plataforma como {ETIQUETA_ROL[sesion.rol].toLowerCase()}: {sesion.nombre}
          </p>
        )}
      </header>
      <main className="contenido">
        <Outlet />
      </main>
    </div>
  )
}
