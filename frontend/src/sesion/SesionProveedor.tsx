import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { CLAVE_SESION as CLAVE, Contexto, EVENTO_SESION_VENCIDA, type Sesion } from './contexto.ts'

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
      typeof dato.token === 'string' &&
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

  // Si el servidor responde 401 (token vencido o alterado), se cierra la sesión y
  // RequiereRol lleva a la pantalla de ingreso.
  useEffect(() => {
    window.addEventListener(EVENTO_SESION_VENCIDA, cerrar)
    return () => window.removeEventListener(EVENTO_SESION_VENCIDA, cerrar)
  }, [cerrar])

  const valor = useMemo(() => ({ sesion, iniciar, cerrar }), [sesion, iniciar, cerrar])
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}
