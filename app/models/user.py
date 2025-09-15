from datetime import datetime
from ..extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # admin|driver|passenger
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True, unique=True)
    phone = db.Column(db.String(30), nullable=False)
    whatsapp = db.Column(db.String(30), nullable=True)
    address = db.Column(db.String(255), nullable=False)
    lat = db.Column(db.Float, nullable=True)
    lon = db.Column(db.Float, nullable=True)
    has_vehicle = db.Column(db.Boolean, default=False)
    can_drive = db.Column(db.Boolean, default=False)
    capacity = db.Column(db.Integer, default=0)
    wants_ride = db.Column(db.Boolean, default=False)
    is_available = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Auth helpers
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
