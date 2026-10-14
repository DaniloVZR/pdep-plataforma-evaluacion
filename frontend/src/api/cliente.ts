import type { ErrorRespuesta } from './tipos'

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
  let respuesta: Response
  try {
    respuesta = await fetch(ruta, {
      method: metodo,
      headers: cuerpo === undefined ? undefined : { 'Content-Type': 'application/json' },
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
