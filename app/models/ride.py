from datetime import datetime
from ..extensions import db

class RideRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending|assigned|canceled|completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), default="assigned")  # assigned|enroute|arrived|completed|canceled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RidePassenger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey("ride.id"), nullable=False)
    passenger_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
