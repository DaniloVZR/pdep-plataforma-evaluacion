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

async function solicitar<T>(metodo: Metodo, ruta: string, cuerpo?: unknown): Promise<T> {
  const encabezados: Record<string, string> = {}
  if (cuerpo !== undefined) encabezados['Content-Type'] = 'application/json'
  const token = tokenGuardado()
  if (token) encabezados.Authorization = `Bearer ${token}`

  let respuesta: Response
  try {
    respuesta = await fetch(ruta, {
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

  // Si el servidor falla sin pasar por el manejador de errores, el cuerpo no es JSON.
  const datos: unknown = await respuesta.json().catch(() => null)

  if (!respuesta.ok) {
    const error = datos as Partial<ErrorRespuesta> | null
    // 401 por token vencido o alterado: se cierra la sesión (el de login es otro código).
    if (respuesta.status === 401 && error?.codigo === 'sesion_requerida') {
      window.dispatchEvent(new Event(EVENTO_SESION_VENCIDA))
    }
    throw new ErrorApi(
      respuesta.status,
      error?.codigo ?? 'error_desconocido',
      error?.mensaje ?? 'Ocurrió un error inesperado. Inténtalo de nuevo.',
    )
  }
  return datos as T
}

export const api = {
  get: <T>(ruta: string) => solicitar<T>('GET', ruta),
  post: <T>(ruta: string, cuerpo: unknown) => solicitar<T>('POST', ruta, cuerpo),
  put: <T>(ruta: string, cuerpo: unknown) => solicitar<T>('PUT', ruta, cuerpo),
}
