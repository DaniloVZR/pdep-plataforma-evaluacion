"""Inicio de sesión con roles (RNF-03).

Versión sencilla para el prototipo: compara la clave guardada con la recibida y
devuelve la cuenta con su rol. No emite tokens; el frontend guarda la sesión.
"""

from app.dominio.errores import CredencialesInvalidasError
from app.dominio.modelos import Cuenta
from app.repositorios.contratos import CuentaRepositorio
from app.validadores.sesion_validador import validar_datos_login
from app.validadores.usuario_validador import normalizar_correo

MENSAJE_CREDENCIALES = "Correo o contraseña incorrectos."


class SesionServicio:
    """Verifica las credenciales contra las cuentas registradas."""

    def __init__(self, cuenta_repo: CuentaRepositorio) -> None:
        self._cuenta_repo = cuenta_repo

    def iniciar_sesion(self, datos: object) -> Cuenta:
        """Devuelve la cuenta si el correo existe y la clave coincide.

        El correo se normaliza igual que en HU-003, así que ``ANA@...`` entra con la
        cuenta de ``ana@...``. La clave se compara tal cual: distingue mayúsculas.
        """
        validar_datos_login(datos)                                       # D1
        cuenta = self._cuenta_repo.buscar_por_correo(normalizar_correo(datos["correo"]))
        if cuenta is None or cuenta.clave != datos["clave"]:             # D2
            raise CredencialesInvalidasError(MENSAJE_CREDENCIALES)
        return cuenta
