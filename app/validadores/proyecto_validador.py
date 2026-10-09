"""Validaciones de la inscripción de proyectos (HU-005)."""

from app.dominio.errores import DatoInvalidoError
from app.dominio.modelos import Modalidad
from app.validadores.comunes import es_entero_positivo, es_lista_de_ids, es_texto_no_vacio


def validar_datos_inscripcion(datos: object) -> None:
    """Lanza ``DatoInvalidoError`` si la solicitud de inscripción está mal formada.

    Además de los tipos, aplica RN009: un Proyecto de Aula (PA) va en una sola
    asignatura y un Proyecto Integrador (PIA) en dos o más.
    """
    if not isinstance(datos, dict):
        raise DatoInvalidoError("El cuerpo de la solicitud debe ser un objeto JSON.")
    for campo in ("equipo_id", "feria_id"):
        if not es_entero_positivo(datos.get(campo)):
            raise DatoInvalidoError(f"El campo '{campo}' debe ser un entero positivo.")
    if not es_texto_no_vacio(datos.get("nombre")):
        raise DatoInvalidoError("El campo 'nombre' es obligatorio y debe ser texto.")
    if datos.get("modalidad") not in {modalidad.value for modalidad in Modalidad}:
        raise DatoInvalidoError("La modalidad debe ser PA o PIA.")
    asignaturas = datos.get("asignatura_ids")
    if not es_lista_de_ids(asignaturas) or not asignaturas:
        raise DatoInvalidoError("'asignatura_ids' debe ser una lista no vacía de enteros.")
    cantidad = len(set(asignaturas))
    if datos["modalidad"] == Modalidad.PA.value and cantidad != 1:
        raise DatoInvalidoError("Un Proyecto de Aula (PA) se inscribe en una sola asignatura.")
    if datos["modalidad"] == Modalidad.PIA.value and cantidad < 2:
        raise DatoInvalidoError("Un Proyecto Integrador (PIA) requiere dos o más asignaturas.")


def normalizar_nombre(nombre: str) -> str:
    """Nombre en minúsculas y con espacios simples, para detectar duplicados (RN002).

    ``"  Robot   Clasificador "`` y ``"robot clasificador"`` son el mismo proyecto.
    """
    return " ".join(nombre.split()).lower()
