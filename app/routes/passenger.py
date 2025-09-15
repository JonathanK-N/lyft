from flask import Blueprint, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.user import User
from ..models.ride import Ride, RidePassenger, RideRequest
from ..utils.geolocation import distance_km

bp = Blueprint("passenger", __name__)

@bp.get("/")
def passenger_portal_page():
    # Page UI passager (les appels API nécessitent un JWT)
    from ..config import Config
    return render_template("portal_passenger.html", church_lat=Config.CHURCH_LAT, church_lon=Config.CHURCH_LON)

def nearest_available_driver(passenger: User):
    drivers = User.query.filter_by(role="driver", is_available=True).all()
    best, bestd = None, 1e18
    for d in drivers:
        if d.lat is None or d.lon is None or (d.capacity or 0) <= 0:
            continue
        dk = distance_km((d.lat,d.lon), (passenger.lat,passenger.lon)) if passenger.lat and passenger.lon else 1e17
        if dk < bestd:
            best, bestd = d, dk
    return best, bestd

@bp.post("/request")
@jwt_required()
def request_ride():
    uid = int(get_jwt_identity())
    p = User.query.get_or_404(uid)
    if p.role != "passenger":
        return jsonify({"error":"not a passenger"}), 403

    rr = RideRequest(passenger_id=p.id, status="pending")
    db.session.add(rr); db.session.commit()

    d, dkm = nearest_available_driver(p)
    if not d:
        return jsonify({"error":"no available driver"}), 200

    d.capacity = max(0, (d.capacity or 0) - 1)
    ride = Ride(driver_id=d.id, status="assigned")
    db.session.add(ride); db.session.flush()
    db.session.add(RidePassenger(ride_id=ride.id, passenger_id=p.id))
    rr.status = "assigned"
    db.session.commit()

    return jsonify({
        "driver": {"id": d.id, "name": d.name, "phone": d.phone, "whatsapp": d.whatsapp or d.phone, "address": d.address, "lat": d.lat, "lon": d.lon},
        "distance_km": dkm
    })
