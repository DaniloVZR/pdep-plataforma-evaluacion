import { useSearchParams } from 'react-router-dom'
import { listarInstituciones } from '../api/endpoints.ts'
import { useConsulta } from './useConsulta.ts'

const cargarInstituciones = () => listarInstituciones()

/**
 * Institución con la que se trabaja en las pantallas de HU-001. Se guarda en la URL
 * (`?institucion=2`) para que no se pierda al pasar de una pantalla a otra con el menú
 * rápido. Si no hay ninguna elegida, se usa la primera de la lista.
 */
export function useInstitucionElegida() {
  const instituciones = useConsulta(cargarInstituciones)
  const [parametros, setParametros] = useSearchParams()
  const pedida = Number(parametros.get('institucion'))
  const institucion =
    instituciones.datos?.find((i) => i.id === pedida) ?? instituciones.datos?.[0] ?? null

  const elegir = (id: number) => setParametros({ institucion: String(id) }, { replace: true })

  return { instituciones, institucion, elegir }
}
