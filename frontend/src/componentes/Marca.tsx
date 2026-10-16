import { GraduationCap } from 'lucide-react'
import { Link } from 'react-router-dom'

/** Nombre de la plataforma con su ícono; lleva a `a` al hacer clic. */
export function Marca({ a = '/' }: { a?: string }) {
  return (
    <Link to={a} className="marca" aria-label="PDEP, evaluación de proyectos institucionales">
      <span className="marca-icono">
        <GraduationCap size={22} aria-hidden="true" />
      </span>
      <span className="marca-texto">
        <strong>PDEP</strong>
        <span>Evaluación de proyectos</span>
      </span>
    </Link>
  )
}
