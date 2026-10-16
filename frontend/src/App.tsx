import { Link, Route, Routes } from 'react-router-dom'
import { LayoutApp } from './componentes/LayoutApp.tsx'
import { LayoutPublico } from './componentes/LayoutPublico.tsx'
import { RequiereRol } from './componentes/RequiereRol.tsx'
import { Landing } from './paginas/Landing.tsx'
import { Login } from './paginas/Login.tsx'
import { PanelAdmin } from './paginas/PanelAdmin.tsx'
import { Pendiente } from './paginas/Pendiente.tsx'

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
              <Pendiente titulo="Registrar usuario" historia="HU-003" />
            </RequiereRol>
          }
        />
        <Route
          path="proyectos/inscribir"
          element={
            <RequiereRol roles={['ESTUDIANTE']}>
              <Pendiente titulo="Inscribir proyecto" historia="HU-005" />
            </RequiereRol>
          }
        />
        <Route
          path="evaluaciones"
          element={
            <RequiereRol roles={['EVALUADOR']}>
              <Pendiente titulo="Mis evaluaciones" historia="HU-007" />
            </RequiereRol>
          }
        />
        <Route
          path="evaluaciones/:proyectoId"
          element={
            <RequiereRol roles={['EVALUADOR']}>
              <Pendiente titulo="Calificar proyecto" historia="HU-007" />
            </RequiereRol>
          }
        />
        <Route
          path="proyectos"
          element={
            <RequiereRol roles={['ADMINISTRADOR', 'EVALUADOR', 'ESTUDIANTE']}>
              <Pendiente titulo="Proyectos" historia="listado" />
            </RequiereRol>
          }
        />
      </Route>
    </Routes>
  )
}
