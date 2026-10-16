import { Building2, CalendarDays, ListChecks, UserCheck, type LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

interface Funcion {
  titulo: string
  texto: string
  icono: LucideIcon
}

const FUNCIONES: Funcion[] = [
  {
    titulo: 'Registro de estructura académica',
    texto: 'Instituciones, programas, asignaturas, estudiantes y docentes en un solo lugar.',
    icono: Building2,
  },
  {
    titulo: 'Gestión de eventos',
    texto: 'Crea ferias con fechas, asignaturas participantes y plazos de inscripción.',
    icono: CalendarDays,
  },
  {
    titulo: 'Asignación de evaluadores',
    texto: 'Reparte los proyectos entre jurados sin sobrecargar a ninguno.',
    icono: UserCheck,
  },
  {
    titulo: 'Rúbricas digitales',
    texto: 'Califica por criterios con peso y obtén el puntaje final calculado automáticamente.',
    icono: ListChecks,
  },
]

// Ejemplo ilustrativo con los datos de demostración del backend.
const EJEMPLO = [
  { criterio: 'Funcionalidad', peso: 50, nota: 4.0 },
  { criterio: 'Calidad del código', peso: 30, nota: 3.0 },
  { criterio: 'Presentación', peso: 20, nota: 5.0 },
]

export function Landing() {
  return (
    <>
      <section className="hero">
        <div className="hero-contenido">
          <div className="hero-texto">
            <h1>Evaluación de Proyectos Institucionales</h1>
            <p className="hero-subtitulo">
              Centralizando y digitalizando la gestión de ferias y eventos académicos
            </p>
            <Link to="/ingresar" className="boton boton-naranja boton-grande">
              Iniciar sesión
            </Link>
          </div>

          <figure className="rubrica-ejemplo" aria-label="Ejemplo de una rúbrica con su puntaje">
            <figcaption>Ejemplo de rúbrica</figcaption>
            <ul>
              {EJEMPLO.map((fila) => (
                <li key={fila.criterio}>
                  <span className="rubrica-criterio">
                    {fila.criterio} <small>{fila.peso} %</small>
                  </span>
                  <span className="rubrica-barra" aria-hidden="true">
                    <span style={{ width: `${(fila.nota / 5) * 100}%` }} />
                  </span>
                  <span className="rubrica-nota">{fila.nota.toFixed(1)}</span>
                </li>
              ))}
            </ul>
            <p className="rubrica-total">
              <span>Puntaje final</span>
              <strong>3.9</strong>
            </p>
          </figure>
        </div>
      </section>

      <section className="funciones">
        <div className="funciones-contenido">
          <h2>¿Qué permite la plataforma?</h2>
          <ul className="funciones-lista">
            {FUNCIONES.map(({ titulo, texto, icono: Icono }) => (
              <li key={titulo}>
                <span className="funcion-icono">
                  <Icono size={24} aria-hidden="true" />
                </span>
                <h3>{titulo}</h3>
                <p>{texto}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </>
  )
}
