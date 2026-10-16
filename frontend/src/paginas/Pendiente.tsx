/** Marcador de las pantallas que se construyen en los siguientes pasos. */
export function Pendiente({ titulo, historia }: { titulo: string; historia: string }) {
  return (
    <section>
      <h1>{titulo}</h1>
      <p className="estado">Esta pantalla ({historia}) se construye en el siguiente paso.</p>
    </section>
  )
}
