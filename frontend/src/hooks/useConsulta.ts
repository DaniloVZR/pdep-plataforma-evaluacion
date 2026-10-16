import { useEffect, useState } from 'react'
import { ErrorApi } from '../api/cliente.ts'

interface Resultado<T> {
  /** Consulta y número de intento a los que pertenece este resultado. */
  origen: () => Promise<T>
  intento: number
  datos: T | null
  error: ErrorApi | null
}

/**
 * Ejecuta una consulta al montar la pantalla (y cada vez que cambie `cargar`).
 * `cargar` debe ser estable: defínela fuera del componente o con `useCallback`.
 * "Cargando" se deduce de si el último resultado corresponde a la consulta actual.
 */
export function useConsulta<T>(cargar: () => Promise<T>) {
  const [resultado, setResultado] = useState<Resultado<T> | null>(null)
  const [intento, setIntento] = useState(0)

  useEffect(() => {
    let vigente = true
    cargar()
      .then((datos) => {
        if (vigente) setResultado({ origen: cargar, intento, datos, error: null })
      })
      .catch((causa: unknown) => {
        if (!vigente) return
        const error =
          causa instanceof ErrorApi
            ? causa
            : new ErrorApi(0, 'error_desconocido', 'Ocurrió un error inesperado.')
        setResultado({ origen: cargar, intento, datos: null, error })
      })
    return () => {
      vigente = false
    }
  }, [cargar, intento])

  const cargando =
    resultado === null || resultado.origen !== cargar || resultado.intento !== intento
  return {
    cargando,
    datos: cargando ? null : resultado.datos,
    error: cargando ? null : resultado.error,
    recargar: () => setIntento((n) => n + 1),
  }
}
