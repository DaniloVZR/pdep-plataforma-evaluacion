import { Link, Route, Routes } from 'react-router-dom'
import { LayoutApp } from './componentes/LayoutApp.tsx'
import { LayoutPublico } from './componentes/LayoutPublico.tsx'
import { RequiereRol } from './componentes/RequiereRol.tsx'
import { Landing } from './paginas/Landing.tsx'
import { Login } from './paginas/Login.tsx'
import { PanelAdmin } from './paginas/PanelAdmin.tsx'
import { CalificarProyecto } from './paginas/CalificarProyecto.tsx'
import { InscribirProyecto } from './paginas/InscribirProyecto.tsx'
import { ListadoProyectos } from './paginas/ListadoProyectos.tsx'
import { MisEvaluaciones } from './paginas/MisEvaluaciones.tsx'
import { RegistrarUsuario } from './paginas/RegistrarUsuario.tsx'
import './pantallas.css'

function NoEncontrada() {
  return (
    <section className="pagina-simple">
      <h1>No encontramos esa página</h1>
      <p>
        <Link to="/">Volver al inicio</Link>
      </p>
    </section>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<LayoutPublico />}>
        <Route index element={<Landing />} />
        <Route path="*" element={<NoEncontrada />} />
      </Route>
      <Route path="ingresar" element={<Login />} />

      <Route element={<LayoutApp />}>
        <Route
          path="admin"
          element={
            <RequiereRol roles={['ADMINISTRADOR']}>
              <PanelAdmin />
            </RequiereRol>
          }
        />
        <Route
          path="usuarios/nuevo"
          element={
            <RequiereRol roles={['ADMINISTRADOR']}>
              <RegistrarUsuario />
            </RequiereRol>
          }
        />
        <Route
          path="proyectos/inscribir"
          element={
            <RequiereRol roles={['ESTUDIANTE']}>
              <InscribirProyecto />
            </RequiereRol>
          }
        />
        <Route
          path="evaluaciones"
          element={
            <RequiereRol roles={['EVALUADOR']}>
              <MisEvaluaciones />
            </RequiereRol>
          }
        />
        <Route
          path="evaluaciones/:proyectoId"
          element={
            <RequiereRol roles={['EVALUADOR']}>
              <CalificarProyecto />
            </RequiereRol>
          }
        />
        <Route
          path="proyectos"
          element={
            <RequiereRol roles={['ADMINISTRADOR', 'EVALUADOR', 'ESTUDIANTE']}>
              <ListadoProyectos />
            </RequiereRol>
          }
        />
      </Route>
    </Routes>
  )
}
