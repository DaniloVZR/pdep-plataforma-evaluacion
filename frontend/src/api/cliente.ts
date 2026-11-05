import { CLAVE_SESION, EVENTO_SESION_VENCIDA } from '../sesion/contexto.ts'
import type { ErrorRespuesta } from './tipos'

/** Token de la sesión guardada, o null si no hay sesión (PDEP-47). */
function tokenGuardado(): string | null {
  try {
    const texto = localStorage.getItem(CLAVE_SESION)
    const sesion = texto ? (JSON.parse(texto) as { token?: unknown }) : null
    return typeof sesion?.token === 'string' ? sesion.token : null
  } catch {
    return null
  }
}

/** Error devuelto por el backend (o por la red) con su código y mensaje. */
export class ErrorApi extends Error {
  readonly estado: number
  readonly codigo: string

  constructor(estado: number, codigo: string, mensaje: string) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.estado = estado
    this.codigo = codigo
  }
}

type Metodo = 'GET' | 'POST' | 'PUT'

/** Hace la petición con el token de la sesión; si la red falla, lanza `sin_conexion`. */
async function enviar(metodo: Metodo, ruta: string, cuerpo?: unknown): Promise<Response> {
  const encabezados: Record<string, string> = {}
  if (cuerpo !== undefined) encabezados['Content-Type'] = 'application/json'
  const token = tokenGuardado()
  if (token) encabezados.Authorization = `Bearer ${token}`
  try {
    return await fetch(ruta, {
      method: metodo,
      headers: encabezados,
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    })
  } catch {
    throw new ErrorApi(
      0,
      'sin_conexion',
      'No se pudo conectar con el servidor. Verifica que el backend esté en ejecución.',
    )
  }
}

/** Convierte una respuesta de error del backend en un ErrorApi. */
function comoError(respuesta: Response, datos: unknown): ErrorApi {
  const error = datos as Partial<ErrorRespuesta> | null
  // 401 por token vencido o alterado: se cierra la sesión (el de login es otro código).
  if (respuesta.status === 401 && error?.codigo === 'sesion_requerida') {
    window.dispatchEvent(new Event(EVENTO_SESION_VENCIDA))
  }
  return new ErrorApi(
    respuesta.status,
    error?.codigo ?? 'error_desconocido',
    error?.mensaje ?? 'Ocurrió un error inesperado. Inténtalo de nuevo.',
  )
}

async function solicitar<T>(metodo: Metodo, ruta: string, cuerpo?: unknown): Promise<T> {
  const respuesta = await enviar(metodo, ruta, cuerpo)
  // Si el servidor falla sin pasar por el manejador de errores, el cuerpo no es JSON.
  const datos: unknown = await respuesta.json().catch(() => null)
  if (!respuesta.ok) throw comoError(respuesta, datos)
  return datos as T
}

/**
 * Descarga un archivo (por ejemplo el Excel de HU-010) con la sesión y lo guarda con el
 * nombre que manda el servidor en `Content-Disposition`.
 */
async function descargar(ruta: string): Promise<void> {
  const respuesta = await enviar('GET', ruta)
  if (!respuesta.ok) throw comoError(respuesta, await respuesta.json().catch(() => null))
  const nombre =
    /filename="([^"]+)"/.exec(respuesta.headers.get('Content-Disposition') ?? '')?.[1] ??
    'reporte.xlsx'
  const enlace = document.createElement('a')
  enlace.href = URL.createObjectURL(await respuesta.blob())
  enlace.download = nombre
  enlace.click()
  // Se libera después: si se libera de inmediato, algunos navegadores cancelan la descarga.
  setTimeout(() => URL.revokeObjectURL(enlace.href), 1000)
}

export const api = {
  get: <T>(ruta: string) => solicitar<T>('GET', ruta),
  post: <T>(ruta: string, cuerpo: unknown) => solicitar<T>('POST', ruta, cuerpo),
  put: <T>(ruta: string, cuerpo: unknown) => solicitar<T>('PUT', ruta, cuerpo),
  descargar,
}
