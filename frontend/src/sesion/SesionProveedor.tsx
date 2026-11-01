import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { Contexto, type Sesion } from './contexto.ts'

const CLAVE = 'pdep.sesion'
const ROLES = ['ADMINISTRADOR', 'EVALUADOR', 'ESTUDIANTE']

function leerSesionGuardada(): Sesion | null {
  try {
    const texto = localStorage.getItem(CLAVE)
    if (texto === null) return null
    const dato = JSON.parse(texto) as Partial<Sesion> | null
    const valida =
      dato !== null &&
      typeof dato.rol === 'string' &&
      ROLES.includes(dato.rol) &&
      typeof dato.rolCuenta === 'string' &&
      ROLES.includes(dato.rolCuenta) &&
      typeof dato.nombre === 'string' &&
      typeof dato.cuenta === 'string' &&
      (dato.usuarioId === null || typeof dato.usuarioId === 'number')
    return valida ? (dato as Sesion) : null
  } catch {
    return null
  }
}

export function SesionProveedor({ children }: { children: ReactNode }) {
  const [sesion, setSesion] = useState<Sesion | null>(leerSesionGuardada)

  const iniciar = useCallback((nueva: Sesion) => {
    setSesion(nueva)
    try {
      localStorage.setItem(CLAVE, JSON.stringify(nueva))
    } catch {
      // Sin almacenamiento disponible la sesión dura hasta recargar la página.
    }
  }, [])

  const cerrar = useCallback(() => {
    setSesion(null)
    try {
      localStorage.removeItem(CLAVE)
    } catch {
      // Nada que borrar.
    }
  }, [])

  const valor = useMemo(() => ({ sesion, iniciar, cerrar }), [sesion, iniciar, cerrar])
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}
