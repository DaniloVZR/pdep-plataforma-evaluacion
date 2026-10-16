import { createContext, useContext } from 'react'

export type RolSesion = 'ADMINISTRADOR' | 'EVALUADOR' | 'ESTUDIANTE'

/**
 * Sesión simulada: el backend todavía no tiene inicio de sesión (RNF-03), así que
 * el frontend recuerda qué rol y qué usuario eligió la persona.
 */
export interface Sesion {
  rol: RolSesion
  /** null para el administrador, que no corresponde a un usuario registrado. */
  usuarioId: number | null
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
  ADMINISTRADOR: '/usuarios/nuevo',
  EVALUADOR: '/evaluaciones',
  ESTUDIANTE: '/proyectos/inscribir',
}
