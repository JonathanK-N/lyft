from flask import Blueprint
from .auth import bp as auth_bp
from .portal import bp as portal_bp
from .driver import bp as driver_bp
from .passenger import bp as passenger_bp
from .admin import bp as admin_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(portal_bp)
    app.register_blueprint(driver_bp, url_prefix="/driver")
    app.register_blueprint(passenger_bp, url_prefix="/passenger")
    app.register_blueprint(admin_bp, url_prefix="/admin")
