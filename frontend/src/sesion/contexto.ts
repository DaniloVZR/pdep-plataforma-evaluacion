import { createContext, useContext } from 'react'
import type { RolCuenta } from '../api/tipos.ts'

export type RolSesion = RolCuenta

/**
 * Sesión iniciada con `POST /api/login` (RNF-03). Se llena con la respuesta del
 * servidor y se guarda en el navegador hasta cerrar sesión.
 */
export interface Sesion {
  /** Nombre de la cuenta que inició sesión (lo que se ve en "Bienvenido, ..."). */
  cuenta: string
  /** Rol real de la cuenta. No cambia con "Ver como". */
  rolCuenta: RolSesion
  /** Vista activa. Solo el administrador puede cambiarla con "Ver como". */
  rol: RolSesion
  /** Usuario del backend que se está simulando; null para el administrador. */
  usuarioId: number | null
  /** Nombre de la persona de la vista activa. */
  nombre: string
}

export interface SesionContexto {
  sesion: Sesion | null
  iniciar: (sesion: Sesion) => void
  cerrar: () => void
}

export const Contexto = createContext<SesionContexto | null>(null)

export function useSesion(): SesionContexto {
  const contexto = useContext(Contexto)
  if (contexto === null) {
    throw new Error('useSesion debe usarse dentro de <SesionProveedor>.')
  }
  return contexto
}

export const ETIQUETA_ROL: Record<RolSesion, string> = {
  ADMINISTRADOR: 'Administrador',
  EVALUADOR: 'Evaluador',
  ESTUDIANTE: 'Estudiante',
}

/** Primera pantalla de cada rol después de entrar. */
export const RUTA_INICIAL: Record<RolSesion, string> = {
  ADMINISTRADOR: '/admin',
  EVALUADOR: '/evaluaciones',
  ESTUDIANTE: '/proyectos/inscribir',
}
