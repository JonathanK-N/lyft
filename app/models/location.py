from datetime import datetime
from ..extensions import db

class LocationPing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    ts = db.Column(db.DateTime, default=datetime.utcnow)
