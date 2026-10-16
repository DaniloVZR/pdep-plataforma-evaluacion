import { UserPlus } from 'lucide-react'
import { useId, useState, type SyntheticEvent } from 'react'
import type { ErrorApi } from '../api/cliente.ts'
import { listarProgramas, registrarUsuario } from '../api/endpoints.ts'
import type { Rol, Usuario } from '../api/tipos.ts'
import { Cargando, MensajeError } from '../componentes/Estados.tsx'
import { useConsulta } from '../hooks/useConsulta.ts'
import { comoErrorApi } from '../utilidades.ts'

const cargarProgramas = () => listarProgramas()

/**
 * HU-003 · El administrador registra estudiantes y docentes.
 * Aquí solo se revisa que los campos estén llenos: el dominio institucional (RN001)
 * y el correo duplicado los decide el backend y su mensaje se muestra tal cual.
 */
export function RegistrarUsuario() {
  const id = useId()
  const programas = useConsulta(cargarProgramas)

  const [nombres, setNombres] = useState('')
  const [correo, setCorreo] = useState('')
  const [rol, setRol] = useState<Rol>('ESTUDIANTE')
  const [programaId, setProgramaId] = useState('')
  const [asignaturaIds, setAsignaturaIds] = useState<number[]>([])

  const [intentado, setIntentado] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [errorServidor, setErrorServidor] = useState<ErrorApi | null>(null)
  const [creado, setCreado] = useState<Usuario | null>(null)

  const programa = programas.datos?.find((p) => String(p.id) === programaId)

  const errores = {
    nombres: nombres.trim() ? '' : 'Escribe los nombres de la persona.',
    correo: !correo.trim()
      ? 'Escribe el correo institucional.'
      : !correo.includes('@')
        ? 'El correo debe tener una @.'
        : '',
    programa: programaId ? '' : 'Elige el programa académico.',
  }
  const hayErrores = Object.values(errores).some(Boolean)

  function alternarAsignatura(asignaturaId: number) {
    setAsignaturaIds((actuales) =>
      actuales.includes(asignaturaId)
        ? actuales.filter((a) => a !== asignaturaId)
        : [...actuales, asignaturaId],
    )
  }

  function limpiar() {
    setNombres('')
    setCorreo('')
    setRol('ESTUDIANTE')
    setProgramaId('')
    setAsignaturaIds([])
    setIntentado(false)
  }

  async function guardar(evento: SyntheticEvent<HTMLFormElement>) {
    evento.preventDefault()
    setIntentado(true)
    setCreado(null)
    setErrorServidor(null)
    if (hayErrores) return

    setEnviando(true)
    try {
      const usuario = await registrarUsuario({
        nombres: nombres.trim(),
        correo: correo.trim(),
        rol,
        programa_id: Number(programaId),
        asignatura_ids: asignaturaIds,
      })
      setCreado(usuario)
      limpiar()
    } catch (causa) {
      setErrorServidor(comoErrorApi(causa))
    } finally {
      setEnviando(false)
    }
  }

  const mostrar = (campo: keyof typeof errores) => intentado && errores[campo] !== ''

  return (
    <section className="pantalla">
      <div className="bienvenida">
        <h1>Registrar usuario</h1>
        <p>Registra un estudiante o docente y asócialo a su programa y asignaturas.</p>
      </div>

      {creado && (
        <div className="aviso aviso-exito" role="status">
          <p>
            <strong>{creado.nombres}</strong> quedó registrado como{' '}
            {creado.rol === 'DOCENTE' ? 'docente' : 'estudiante'} con el correo {creado.correo}.
          </p>
        </div>
      )}
      {errorServidor && <MensajeError error={errorServidor} />}

      <form className="tarjeta" onSubmit={guardar} noValidate>
        <fieldset>
          <legend className="tarjeta-subtitulo">Rol</legend>
          <div className="selector-segmentado">
            {(['ESTUDIANTE', 'DOCENTE'] as const).map((r) => (
              <label key={r} className={rol === r ? 'activo' : ''}>
                <input type="radio" name={`${id}-rol`} checked={rol === r} onChange={() => setRol(r)} />
                {r === 'ESTUDIANTE' ? 'Estudiante' : 'Docente'}
              </label>
            ))}
          </div>
        </fieldset>

        <div className="rejilla-2">
          <div className="campo">
            <label htmlFor={`${id}-nombres`}>Nombres completos</label>
            <input
              id={`${id}-nombres`}
              type="text"
              value={nombres}
              onChange={(e) => setNombres(e.target.value)}
              aria-invalid={mostrar('nombres')}
            />
            {mostrar('nombres') && <p className="campo-error">{errores.nombres}</p>}
          </div>

          <div className="campo">
            <label htmlFor={`${id}-correo`}>Correo institucional</label>
            <input
              id={`${id}-correo`}
              type="email"
              placeholder="nombre@pascualbravo.edu.co"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              aria-invalid={mostrar('correo')}
            />
            {mostrar('correo') && <p className="campo-error">{errores.correo}</p>}
          </div>
        </div>

        <div className="campo">
          <label htmlFor={`${id}-programa`}>Programa académico</label>
          {programas.cargando ? (
            <Cargando texto="Cargando programas…" />
          ) : programas.error ? (
            <MensajeError error={programas.error} alReintentar={programas.recargar} />
          ) : (
            <select
              id={`${id}-programa`}
              value={programaId}
              onChange={(e) => {
                setProgramaId(e.target.value)
                setAsignaturaIds([])
              }}
              aria-invalid={mostrar('programa')}
            >
              <option value="">Selecciona un programa</option>
              {programas.datos?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre}
                </option>
              ))}
            </select>
          )}
          {mostrar('programa') && <p className="campo-error">{errores.programa}</p>}
        </div>

        {programa && (
          <fieldset>
            <legend className="tarjeta-subtitulo">
              Asignaturas {rol === 'DOCENTE' ? 'que dicta' : 'que cursa'} <small>(opcional)</small>
            </legend>
            {programa.asignaturas.length === 0 ? (
              <p className="estado">Este programa no tiene asignaturas registradas.</p>
            ) : (
              <ul className="opciones">
                {programa.asignaturas.map((a) => (
                  <li key={a.id}>
                    <label className="opcion">
                      <input
                        type="checkbox"
                        checked={asignaturaIds.includes(a.id)}
                        onChange={() => alternarAsignatura(a.id)}
                      />
                      <span>
                        {a.nombre} <small>{a.codigo} · semestre {a.semestre}</small>
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
            )}
          </fieldset>
        )}

        <div className="acciones">
          <button type="submit" className="boton boton-azul" disabled={enviando}>
            <UserPlus size={18} aria-hidden="true" />
            {enviando ? 'Registrando…' : 'Registrar usuario'}
          </button>
        </div>
      </form>
    </section>
  )
}
