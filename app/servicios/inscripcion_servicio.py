"""Caso de uso HU-005: inscribir un proyecto en una feria."""

from app.dominio.errores import (
    AsignaturaNoParticipanteError,
    ConflictoUnicidadError,
    EquipoNoEncontradoError,
    FeriaNoEncontradaError,
    InscripcionNoAbiertaError,
    PlazoVencidoError,
    ProyectoDuplicadoError,
)
from app.dominio.modelos import Modalidad, Proyecto
from app.repositorios.contratos import EquipoRepositorio, FeriaRepositorio, ProyectoRepositorio
from app.servicios.reloj import Reloj
from app.validadores.proyecto_validador import normalizar_nombre, validar_datos_inscripcion

MENSAJE_DUPLICADO = "El equipo ya inscribió un proyecto con ese nombre en la feria."


class InscripcionServicio:
    """Coordina las validaciones y el registro de un proyecto en una feria."""

    def __init__(self, equipo_repo: EquipoRepositorio, feria_repo: FeriaRepositorio,
                 proyecto_repo: ProyectoRepositorio, reloj: Reloj) -> None:
        self._equipo_repo = equipo_repo
        self._feria_repo = feria_repo
        self._proyecto_repo = proyecto_repo
        self._reloj = reloj

    def inscribir(self, datos: object) -> Proyecto:
        """Valida la solicitud, el plazo y los duplicados, y registra el proyecto.

        El inicio y el fin del plazo se revisan en decisiones separadas para
        poder probar cada límite. Se compara por fecha (``date``), así que el
        último día cuenta completo, hasta las 23:59.
        """
        validar_datos_inscripcion(datos)                                 # D1
        if not self._equipo_repo.existe(datos["equipo_id"]):             # D2
            raise EquipoNoEncontradoError("El equipo indicado no existe.")
        feria = self._feria_repo.obtener(datos["feria_id"])
        if feria is None:                                                # D3
            raise FeriaNoEncontradaError("La feria indicada no existe.")
        asignatura_ids = frozenset(datos["asignatura_ids"])
        if not feria.acepta_asignaturas(asignatura_ids):                 # D4
            raise AsignaturaNoParticipanteError(
                "Alguna asignatura no participa en la feria.")
        hoy = self._reloj.hoy()
        if hoy < feria.fecha_inicio:                                     # D5
            raise InscripcionNoAbiertaError("La inscripción a la feria aún no está abierta.")
        if hoy > feria.fecha_fin:                                        # D6
            raise PlazoVencidoError("El plazo de inscripción de la feria ya venció.")
        nombre_normalizado = normalizar_nombre(datos["nombre"])
        if self._proyecto_repo.existe_en_feria(datos["equipo_id"], nombre_normalizado,
                                               feria.id):               # D7
            raise ProyectoDuplicadoError(MENSAJE_DUPLICADO)
        proyecto = Proyecto(
            id=None,
            equipo_id=datos["equipo_id"],
            feria_id=feria.id,
            nombre=" ".join(datos["nombre"].split()),
            descripcion=str(datos.get("descripcion", "")).strip(),
            modalidad=Modalidad(datos["modalidad"]),
            asignatura_ids=tuple(sorted(asignatura_ids)),
            fecha_inscripcion=hoy,
        )
        try:
            return self._proyecto_repo.registrar(proyecto, nombre_normalizado)
        except ConflictoUnicidadError as error:                           # D8
            raise ProyectoDuplicadoError(MENSAJE_DUPLICADO) from error
