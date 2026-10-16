import { ErrorApi } from './api/cliente.ts'
import type { EstadoEvaluacion, Modalidad } from './api/tipos.ts'

/** Convierte cualquier error atrapado en un ErrorApi para mostrarlo con <MensajeError>. */
export function comoErrorApi(causa: unknown): ErrorApi {
  return causa instanceof ErrorApi
    ? causa
    : new ErrorApi(0, 'error_desconocido', 'Ocurrió un error inesperado. Inténtalo de nuevo.')
}

/** "2026-10-01" → "1 oct 2026". Se lee como fecha local para que no cambie de día. */
export function formatearFecha(fecha: string): string {
  const [anio, mes, dia] = fecha.slice(0, 10).split('-').map(Number)
  return new Date(anio, mes - 1, dia).toLocaleDateString('es-CO', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

/** Fecha y hora completas para la constancia de confirmación (RNF-06). */
export function formatearFechaHora(iso: string): string {
  return new Date(iso).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })
}

/** Fecha de hoy como AAAA-MM-DD en la zona horaria del navegador. */
export const fechaDeHoy = () => new Date().toLocaleDateString('sv-SE')

export const ETIQUETA_MODALIDAD: Record<Modalidad, string> = {
  PA: 'Proyecto de Aula (PA)',
  PIA: 'Proyecto Integrador (PIA)',
}

export const ETIQUETA_ESTADO: Record<EstadoEvaluacion, string> = {
  PENDIENTE: 'Pendiente',
  BORRADOR: 'Borrador',
  CONFIRMADA: 'Confirmada',
}
