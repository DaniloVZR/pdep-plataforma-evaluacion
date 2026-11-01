import { Building2, GraduationCap, Landmark } from 'lucide-react'
import { NavLink, useLocation } from 'react-router-dom'
import type { Institucion } from '../api/tipos.ts'

const SECCIONES = [
  { a: '/estructura/instituciones', texto: 'Instituciones', icono: Landmark },
  { a: '/estructura/facultades', texto: 'Facultades y departamentos', icono: Building2 },
  { a: '/estructura/programas', texto: 'Programas', icono: GraduationCap },
]

/** Menú rápido entre las tres pantallas de HU-001. Conserva la institución elegida. */
export function MenuEstructura() {
  const { search } = useLocation()
  return (
    <nav className="pestanas" aria-label="Estructura académica">
      {SECCIONES.map(({ a, texto, icono: Icono }) => (
        <NavLink key={a} to={{ pathname: a, search }} className="pestana">
          <Icono size={16} aria-hidden="true" /> {texto}
        </NavLink>
      ))}
    </nav>
  )
}

interface PropsSelector {
  id: string
  instituciones: Institucion[]
  elegida: Institucion
  alElegir: (id: number) => void
}

/** Lista desplegable para escoger la institución con la que se trabaja. */
export function SelectorInstitucion({ id, instituciones, elegida, alElegir }: PropsSelector) {
  return (
    <div className="campo filtro">
      <label htmlFor={id}>Institución</label>
      <select id={id} value={elegida.id} onChange={(e) => alElegir(Number(e.target.value))}>
        {instituciones.map((i) => (
          <option key={i.id} value={i.id}>
            {i.nombre}
          </option>
        ))}
      </select>
    </div>
  )
}
