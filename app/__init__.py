"""Fábrica de la aplicación Flask de PDEP."""

from pathlib import Path

from flask import Flask


def create_app(config: dict | None = None) -> Flask:
    """Crea la aplicación. ``config`` permite a las pruebas usar otra base de datos."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(DATABASE=str(Path(app.instance_path) / "pdep.sqlite3"))
    if config:
        app.config.update(config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    return app
