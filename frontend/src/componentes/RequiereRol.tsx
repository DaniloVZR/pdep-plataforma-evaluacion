import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { RUTA_INICIAL, useSesion, type RolSesion } from '../sesion/contexto.ts'

/** Si la vista activa no puede ver la pantalla, la lleva a la suya. */
export function RequiereRol({ roles, children }: { roles: RolSesion[]; children: ReactNode }) {
  const { sesion } = useSesion()
  if (sesion === null) {
    return <Navigate to="/ingresar" replace />
  }
  if (!roles.includes(sesion.rol)) {
    return <Navigate to={RUTA_INICIAL[sesion.rol]} replace />
  }
  return <>{children}</>
}
