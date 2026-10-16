import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { ETIQUETA_ROL, useSesion, type RolSesion } from '../sesion/contexto.ts'

interface Enlace {
  a: string
  texto: string
}

const MENU: Record<RolSesion, Enlace[]> = {
  ADMINISTRADOR: [
    { a: '/usuarios/nuevo', texto: 'Registrar usuario' },
    { a: '/proyectos', texto: 'Proyectos' },
  ],
  EVALUADOR: [
    { a: '/evaluaciones', texto: 'Mis evaluaciones' },
    { a: '/proyectos', texto: 'Proyectos' },
  ],
  ESTUDIANTE: [
    { a: '/proyectos/inscribir', texto: 'Inscribir proyecto' },
    { a: '/proyectos', texto: 'Proyectos' },
  ],
}

export function Layout() {
  const { sesion, cerrar } = useSesion()
  const navegar = useNavigate()

  function cambiarDeRol() {
    cerrar()
    navegar('/')
  }

  return (
    <div className="pagina">
      <header className="barra">
        <div className="barra-contenido">
          <Link to="/" className="marca">
            <span className="marca-sigla">PDEP</span>
            <span className="marca-nombre">Evaluación de proyectos</span>
          </Link>

          {sesion && (
            <>
              <nav className="menu" aria-label="Principal">
                {MENU[sesion.rol].map((enlace) => (
                  <NavLink key={enlace.a} to={enlace.a} end className="menu-enlace">
                    {enlace.texto}
                  </NavLink>
                ))}
              </nav>
              <div className="sesion">
                <span className="sesion-datos">
                  <strong>{sesion.nombre}</strong>
                  <span>{ETIQUETA_ROL[sesion.rol]}</span>
                </span>
                <button type="button" className="boton boton-barra" onClick={cambiarDeRol}>
                  Cambiar de rol
                </button>
              </div>
            </>
          )}
        </div>
      </header>

      <main className="contenido">
        <Outlet />
      </main>

      <footer className="pie">
        Institución Universitaria Pascual Bravo · Ingeniería de Software II
      </footer>
    </div>
  )
}
