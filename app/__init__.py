import os
from flask import Flask
from .config import Config
from .extensions import db, migrate, jwt, socketio
from .routes import register_blueprints
from .sockets import register_socket_handlers
from flask_socketio import SocketIO

socketio = SocketIO(async_mode="threading")   # <-- ajouter ce paramètre

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config())
    socketio.init_app(app, cors_allowed_origins="*")

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Ensure models are imported so Alembic sees all tables
    from . import models  # noqa: F401

    # Blueprints
    register_blueprints(app)

    # Sockets
    register_socket_handlers()

    with app.app_context():
        db.create_all()

    return app
