from flask import Flask

from .routes import bp
from .storage import ensure_storage_files


def create_app(config_object="config"):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_object)
    ensure_storage_files(app.config)
    app.register_blueprint(bp)
    return app
