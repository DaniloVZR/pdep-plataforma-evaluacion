"""Fábrica de la aplicación Flask de PDEP."""

from pathlib import Path

from flask import Flask, jsonify

from app import db
from app.controladores.usuario_controlador import usuarios_bp
from app.dominio.errores import ErrorDominio


def create_app(config: dict | None = None) -> Flask:
    """Crea la aplicación. ``config`` permite a las pruebas usar otra base de datos."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(DATABASE=str(Path(app.instance_path) / "pdep.sqlite3"))
    if config:
        app.config.update(config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.registrar_en(app)
    app.register_blueprint(usuarios_bp)

    @app.errorhandler(ErrorDominio)
    def manejar_error_dominio(error: ErrorDominio):
        """Convierte cualquier excepción del dominio en JSON con su código HTTP."""
        return jsonify({"codigo": error.codigo, "mensaje": error.mensaje}), error.estado_http

    return app
