"""Excepciones del dominio.

Cada regla de negocio que no se cumple lanza su propia excepción. El
controlador no decide el código HTTP: lo lee del atributo ``estado_http``
de la excepción, de modo que cada rama de rechazo se puede probar por
separado sin levantar el servidor.
"""


class ErrorDominio(Exception):
    """Base de todos los errores que la aplicación devuelve al cliente."""

    codigo = "error_dominio"
    estado_http = 400

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class DatoInvalidoError(ErrorDominio):
    """Un dato obligatorio falta, es nulo, está vacío o no tiene el tipo esperado."""

    codigo = "dato_invalido"
    estado_http = 400


class RecursoNoEncontradoError(ErrorDominio):
    """Base de los errores por identificadores que no existen en la base de datos."""

    codigo = "recurso_no_encontrado"
    estado_http = 404


class ProgramaNoEncontradoError(RecursoNoEncontradoError):
    """El programa académico indicado no existe."""

    codigo = "programa_no_encontrado"


class AsignaturaNoEncontradaError(RecursoNoEncontradoError):
    """Una o más asignaturas indicadas no existen."""

    codigo = "asignatura_no_encontrada"


class EquipoNoEncontradoError(RecursoNoEncontradoError):
    """El equipo indicado no existe."""

    codigo = "equipo_no_encontrado"


class FeriaNoEncontradaError(RecursoNoEncontradoError):
    """La feria indicada no existe."""

    codigo = "feria_no_encontrada"


class RubricaNoEncontradaError(RecursoNoEncontradoError):
    """La feria no tiene una rúbrica asociada (RN005)."""

    codigo = "rubrica_no_encontrada"
    estado_http = 422


class ReglaNegocioError(ErrorDominio):
    """Base de los errores por reglas de negocio incumplidas."""

    codigo = "regla_negocio"
    estado_http = 422


class CorreoNoInstitucionalError(ReglaNegocioError):
    """El dominio del correo no pertenece a una institución registrada (RN001)."""

    codigo = "correo_no_institucional"


class AsignaturaNoParticipanteError(ReglaNegocioError):
    """Alguna asignatura del proyecto no participa en la feria."""

    codigo = "asignatura_no_participante"


class InscripcionNoAbiertaError(ReglaNegocioError):
    """La fecha actual es anterior a la fecha de inicio de la feria (RN003)."""

    codigo = "inscripcion_no_abierta"


class PlazoVencidoError(ReglaNegocioError):
    """La fecha actual es posterior a la fecha de fin de la feria (RN003)."""

    codigo = "plazo_vencido"


class RubricaSinCriteriosError(ReglaNegocioError):
    """La rúbrica de la feria no tiene criterios."""

    codigo = "rubrica_sin_criterios"


class PesosInvalidosError(ReglaNegocioError):
    """Los pesos de los criterios no son positivos o no suman 1 (100 %)."""

    codigo = "pesos_invalidos"


class NotasIncompletasError(ReglaNegocioError):
    """Las notas recibidas no corresponden exactamente a los criterios de la rúbrica."""

    codigo = "notas_incompletas"


class TipoNotaInvalidoError(ReglaNegocioError):
    """Una nota no es un número real finito (texto, booleano, nulo o NaN)."""

    codigo = "tipo_nota_invalido"


class NotaFueraDeRangoError(ReglaNegocioError):
    """Una nota está por fuera de la escala de la rúbrica."""

    codigo = "nota_fuera_de_rango"


class ConflictoError(ErrorDominio):
    """Base de los errores por registros duplicados o estados que no permiten el cambio."""

    codigo = "conflicto"
    estado_http = 409


class CorreoDuplicadoError(ConflictoError):
    """Ya existe un usuario con el mismo correo."""

    codigo = "correo_duplicado"


class ProyectoDuplicadoError(ConflictoError):
    """El equipo ya inscribió un proyecto con el mismo nombre en la feria (RN002)."""

    codigo = "proyecto_duplicado"


class EvaluacionYaConfirmadaError(ConflictoError):
    """La evaluación ya fue confirmada y no se puede modificar (RN007)."""

    codigo = "evaluacion_confirmada"


class EvaluadorNoAsignadoError(ErrorDominio):
    """El evaluador no tiene asignado el proyecto (RNF-03)."""

    codigo = "evaluador_no_asignado"
    estado_http = 403


class ErrorPersistencia(ErrorDominio):
    """Falla inesperada de la base de datos. La operación se deshizo."""

    codigo = "error_persistencia"
    estado_http = 500


class ConflictoUnicidadError(Exception):
    """Lo lanza un repositorio cuando la base de datos rechaza un registro duplicado.

    No llega al cliente: el servicio la traduce a la excepción de dominio que
    corresponda. Así el servicio no depende de ``sqlite3``.
    """
