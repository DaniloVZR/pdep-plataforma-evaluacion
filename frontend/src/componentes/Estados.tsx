import type { ErrorApi } from '../api/cliente.ts'

export function Cargando({ texto = 'Cargando…' }: { texto?: string }) {
  return (
    <p className="estado" role="status">
      {texto}
    </p>
  )
}

export function MensajeError({ error, alReintentar }: { error: ErrorApi; alReintentar?: () => void }) {
  return (
    <div className="aviso aviso-error" role="alert">
      <p>{error.message}</p>
      {alReintentar && (
        <button type="button" className="boton boton-secundario" onClick={alReintentar}>
          Reintentar
        </button>
      )}
    </div>
  )
}
