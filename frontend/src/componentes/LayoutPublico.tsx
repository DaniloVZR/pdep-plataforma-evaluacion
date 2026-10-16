import { Link, Outlet } from 'react-router-dom'
import { RUTA_INICIAL, useSesion } from '../sesion/contexto.ts'
import { Marca } from './Marca.tsx'

/** Encabezado y pie de las páginas que no requieren sesión. */
export function LayoutPublico() {
  const { sesion } = useSesion()
  return (
    <div className="pagina">
      <header className="encabezado encabezado-claro">
        <div className="encabezado-contenido">
          <Marca />
          <div className="encabezado-acciones">
            {sesion ? (
              <Link to={RUTA_INICIAL[sesion.rol]} className="boton boton-azul">
                Ir a mi panel
              </Link>
            ) : (
              <>
                <Link to="/ingresar" className="boton boton-contorno">
                  Iniciar sesión
                </Link>
                {/* Por ahora el registro lleva a la página inicial. */}
                <Link to="/" className="boton boton-naranja">
                  Registrarse
                </Link>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="principal">
        <Outlet />
      </main>
      <footer className="pie">
        Institución Universitaria Pascual Bravo · Ingeniería de Software II
      </footer>
    </div>
  )
}
