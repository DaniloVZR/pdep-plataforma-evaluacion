"""Caso de uso HU-004: crear una feria con sus asignaturas y su rúbrica (REQ-7)."""

from app.dominio.errores import (
    AsignaturaNoEncontradaError,
    FechasFeriaInvalidasError,
    InstitucionNoEncontradaError,
    PesosInvalidosError,
)
from app.dominio.modelos import NOTA_MAXIMA, NOTA_MINIMA, Criterio, Feria, Rubrica
from app.repositorios.contratos import CreacionFeriaRepositorio
from app.validadores.estructura_validador import limpiar_texto
from app.validadores.feria_validador import leer_fecha, validar_datos_feria


class FeriaServicio:
    """Coordina las validaciones y el guardado de una feria nueva."""

    def __init__(self, repositorio: CreacionFeriaRepositorio) -> None:
        self._repo = repositorio

    def crear(self, datos: object) -> Feria:
        """Crea la feria con su rúbrica para que HU-005 y HU-007 la usen sin cambios.

        Criterios de aceptación del RT2: fin posterior al inicio y una o varias asignaturas.
        Los pesos se revisan con ``Rubrica.pesos_validos``, la misma regla de HU-007.
        """
        validar_datos_feria(datos)                                       # D1
        inicio, fin = leer_fecha(datos["fecha_inicio"]), leer_fecha(datos["fecha_fin"])
        if fin <= inicio:                                                # D2
            raise FechasFeriaInvalidasError(
                "La fecha de fin debe ser posterior a la fecha de inicio.")
        if not self._repo.existe_institucion(datos["institucion_id"]):  # D3
            raise InstitucionNoEncontradaError("La institución indicada no existe.")
        ids = tuple(datos["asignatura_ids"])
        faltantes = sorted(set(ids) - self._repo.asignaturas_de_institucion(
            datos["institucion_id"], ids))
        if faltantes:                                                    # D4
            raise AsignaturaNoEncontradaError(
                f"Las asignaturas {faltantes} no existen o no son de la institución.")
        criterios = tuple((limpiar_texto(c["nombre"]), float(c["peso"]))
                          for c in datos["criterios"])
        rubrica = Rubrica(0, 0, NOTA_MINIMA, NOTA_MAXIMA,
                          tuple(Criterio(i, n, p) for i, (n, p) in enumerate(criterios)))
        if not rubrica.pesos_validos():                                  # D5
            raise PesosInvalidosError("Los pesos de los criterios deben sumar 100 %.")
        feria = Feria(0, limpiar_texto(datos["nombre"]), inicio, fin, frozenset(ids))
        return self._repo.guardar_feria(datos["institucion_id"], feria, criterios)
