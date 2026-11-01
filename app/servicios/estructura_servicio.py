"""Caso de uso HU-001: registrar institución, facultades, departamentos y programas."""

from app.dominio.errores import (
    ConflictoUnicidadError,
    DepartamentoDuplicadoError,
    DepartamentoNoEncontradoError,
    EstructuraInconsistenteError,
    FacultadDuplicadaError,
    FacultadNoEncontradaError,
    InstitucionDuplicadaError,
    InstitucionNoEncontradaError,
    ProgramaDuplicadoError,
)
from app.dominio.modelos import Departamento, Facultad, Institucion, Programa
from app.repositorios.contratos import EstructuraRepositorio
from app.validadores.estructura_validador import (
    limpiar_texto,
    validar_datos_institucion,
    validar_datos_programa,
    validar_datos_unidad,
)


class EstructuraAcademicaServicio:
    """Coordina las validaciones y el guardado de la estructura académica."""

    def __init__(self, repositorio: EstructuraRepositorio) -> None:
        self._repo = repositorio

    def _exigir_institucion(self, institucion_id: int) -> None:
        if not self._repo.existe_institucion(institucion_id):
            raise InstitucionNoEncontradaError("La institución indicada no existe.")

    def registrar_institucion(self, datos: object) -> Institucion:
        """REQ-1. Rechaza si falta el nombre o el NIT; 409 si el NIT o el dominio ya existen."""
        validar_datos_institucion(datos)                                 # D1
        institucion = Institucion(
            id=None,
            nombre=limpiar_texto(datos["nombre"]),
            nit=datos["nit"].strip(),
            correo_contacto=datos.get("correo_contacto", "").strip().lower(),
            telefono=datos.get("telefono", "").strip(),
            dominio=datos.get("dominio", "").strip().lower(),
        )
        try:
            return self._repo.guardar_institucion(institucion)
        except ConflictoUnicidadError as error:                           # D2
            raise InstitucionDuplicadaError(
                "Ya existe una institución con ese NIT o ese dominio.") from error

    def registrar_facultad(self, datos: object) -> Facultad:
        """REQ-2. Rechaza si falta el nombre; 404 si la institución no existe."""
        validar_datos_unidad(datos, "facultad")                       # D1
        self._exigir_institucion(datos["institucion_id"])                # D2
        try:
            return self._repo.guardar_facultad(
                Facultad(None, datos["institucion_id"], limpiar_texto(datos["nombre"])))
        except ConflictoUnicidadError as error:                           # D3
            raise FacultadDuplicadaError(
                "La institución ya tiene una facultad con ese nombre.") from error

    def registrar_departamento(self, datos: object) -> Departamento:
        """REQ-2. Igual que la facultad."""
        validar_datos_unidad(datos, "departamento")                   # D1
        self._exigir_institucion(datos["institucion_id"])                # D2
        try:
            return self._repo.guardar_departamento(
                Departamento(None, datos["institucion_id"], limpiar_texto(datos["nombre"])))
        except ConflictoUnicidadError as error:                           # D3
            raise DepartamentoDuplicadoError(
                "La institución ya tiene un departamento con ese nombre.") from error

    def registrar_programa(self, datos: object) -> Programa:
        """REQ-3. La facultad y el departamento, si vienen, deben ser de la misma institución."""
        validar_datos_programa(datos)                                    # D1
        institucion_id = datos["institucion_id"]
        self._exigir_institucion(institucion_id)                         # D2
        facultad_id = datos.get("facultad_id")
        if facultad_id is not None:                                      # D3
            duena = self._repo.institucion_de_facultad(facultad_id)
            if duena is None:                                            # D4
                raise FacultadNoEncontradaError("La facultad indicada no existe.")
            if duena != institucion_id:                                  # D5
                raise EstructuraInconsistenteError(
                    "La facultad pertenece a otra institución.")
        departamento_id = datos.get("departamento_id")
        if departamento_id is not None:                                  # D6
            duena = self._repo.institucion_de_departamento(departamento_id)
            if duena is None:                                            # D7
                raise DepartamentoNoEncontradoError("El departamento indicado no existe.")
            if duena != institucion_id:                                  # D8
                raise EstructuraInconsistenteError(
                    "El departamento pertenece a otra institución.")
        programa = Programa(
            id=None,
            institucion_id=institucion_id,
            codigo=datos["codigo"].strip().upper(),
            nombre=limpiar_texto(datos["nombre"]),
            facultad_id=facultad_id,
            departamento_id=departamento_id,
        )
        try:
            return self._repo.guardar_programa(programa)
        except ConflictoUnicidadError as error:                           # D9
            raise ProgramaDuplicadoError("Ya existe un programa con ese código.") from error
