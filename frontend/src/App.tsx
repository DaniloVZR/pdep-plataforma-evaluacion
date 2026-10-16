import { Link, Route, Routes } from 'react-router-dom'
import { Layout } from './componentes/Layout.tsx'
import { RequiereRol } from './componentes/RequiereRol.tsx'
import { Inicio } from './paginas/Inicio.tsx'
import { Pendiente } from './paginas/Pendiente.tsx'

function NoEncontrada() {
  return (
    <section>
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
      <Route element={<Layout />}>
        <Route index element={<Inicio />} />
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
        <Route path="*" element={<NoEncontrada />} />
      </Route>
    </Routes>
  )
}
