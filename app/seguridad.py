"""Control de roles en la API (RNF-03, PDEP-47).

Al iniciar sesión, ``POST /api/login`` entrega un token firmado con el rol y el
usuario de la cuenta. El frontend lo envía en cada petición con el encabezado
``Authorization: Bearer <token>`` y cada endpoint revisa el rol con ``requiere_rol``.

- Sin token, con un token alterado o vencido: 401 (``SesionRequeridaError``).
- Con un rol que no corresponde: 403 (``SinPermisoError``).

El administrador puede usar todos los endpoints, porque con "Ver como" revisa la
plataforma desde la vista de los demás roles.

El token se firma con ``SECRET_KEY`` (itsdangerous viene con Flask). No se guarda en
la base de datos: vence solo a las ``HORAS_SESION`` horas.
"""

from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.dominio.errores import SesionRequeridaError, SinPermisoError
from app.dominio.modelos import Cuenta, RolCuenta

HORAS_SESION = 8
_SAL = "pdep-sesion"
MENSAJE_SIN_SESION = "Debes iniciar sesión para usar esta función."
MENSAJE_SIN_PERMISO = "Tu rol no tiene permiso para hacer esta acción."


def _firmador() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=_SAL)


def emitir_token(cuenta: Cuenta) -> str:
    """Token firmado con el rol y el usuario de la cuenta."""
    return _firmador().dumps({"rol": cuenta.rol.value, "usuario_id": cuenta.usuario_id})


def leer_sesion() -> dict:
    """Lee y verifica el token del encabezado ``Authorization``; si falla, lanza 401."""
    encabezado = request.headers.get("Authorization", "")
    tipo, _, token = encabezado.partition(" ")
    if tipo != "Bearer" or not token:
        raise SesionRequeridaError(MENSAJE_SIN_SESION)
    try:
        datos = _firmador().loads(token, max_age=HORAS_SESION * 3600)
    except BadSignature as error:          # también cubre SignatureExpired
        raise SesionRequeridaError(MENSAJE_SIN_SESION) from error
    return {"rol": RolCuenta(datos["rol"]), "usuario_id": datos["usuario_id"]}


def requiere_rol(*roles: RolCuenta):
    """Deja pasar solo a los roles indicados (y al administrador).

    Sin roles, basta con tener una sesión válida. La sesión queda en ``g.sesion``.
    """
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            exigir_rol(*roles)
            return vista(*args, **kwargs)
        return envoltura
    return decorador


def exigir_rol(*roles: RolCuenta) -> dict:
    """Versión sin decorador de ``requiere_rol``, para usar en ``before_request``."""
    sesion = leer_sesion()
    permitidos = {RolCuenta.ADMINISTRADOR, *roles}
    if roles and sesion["rol"] not in permitidos:
        raise SinPermisoError(MENSAJE_SIN_PERMISO)
    g.sesion = sesion
    return sesion


def exigir_mismo_usuario(usuario_id: object) -> None:
    """Un evaluador o un estudiante solo actúa en su propio nombre.

    Solo compara cuando ``usuario_id`` es un entero: si falta o es inválido, lo
    rechaza después el validador de la historia con su 400 de siempre.
    """
    sesion = g.sesion
    if sesion["rol"] is RolCuenta.ADMINISTRADOR:
        return
    if isinstance(usuario_id, int) and not isinstance(usuario_id, bool) \
            and usuario_id != sesion["usuario_id"]:
        raise SinPermisoError("Solo puedes hacer esta acción en tu propio nombre.")
