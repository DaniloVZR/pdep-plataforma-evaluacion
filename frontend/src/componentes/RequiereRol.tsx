import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useSesion, type RolSesion } from '../sesion/contexto.ts'

/** Lleva al inicio si no hay sesión o el rol elegido no puede ver la pantalla. */
export function RequiereRol({ roles, children }: { roles: RolSesion[]; children: ReactNode }) {
  const { sesion } = useSesion()
  if (sesion === null || !roles.includes(sesion.rol)) {
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}
