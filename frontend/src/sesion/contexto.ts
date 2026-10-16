import { createContext, useContext } from 'react'

export type RolSesion = 'ADMINISTRADOR' | 'EVALUADOR' | 'ESTUDIANTE'

/**
 * Sesión simulada: el backend todavía no tiene inicio de sesión (RNF-03).
 * Cuando exista, el rol saldrá de la cuenta y `Sesion` se llenará con la respuesta del login.
 */
export interface Sesion {
  /** Nombre de la cuenta que inició sesión (lo que se ve en "Bienvenido, ..."). */
  cuenta: string
  /** Vista activa. Con "Ver como" puede ser distinta del rol de la cuenta. */
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
