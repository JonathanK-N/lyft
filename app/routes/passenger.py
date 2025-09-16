from flask import Blueprint, jsonify, render_template, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db, socketio
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
    data = request.get_json() or {}
    plat = data.get("pickup_lat")
    plon = data.get("pickup_lon")

    # Met à jour la position du passager si fournie
    if plat is not None and plon is not None:
        try:
            p.lat = float(plat); p.lon = float(plon)
            db.session.commit()
        except Exception:
            db.session.rollback()

    rr = RideRequest(passenger_id=p.id, status="pending", pickup_lat=p.lat, pickup_lon=p.lon)
    db.session.add(rr); db.session.commit()
    # Diffusion en temps réel aux chauffeurs
    payload = {"request_id": rr.id, "passenger_id": p.id, "name": p.name, "pickup": {"lat": rr.pickup_lat, "lon": rr.pickup_lon}}
    socketio.emit("request:new", payload)

    return jsonify({"ok": True, "request_id": rr.id, "message": "Demande créée. En attente d'un chauffeur."})


@bp.post("/location")
@jwt_required()
def update_location():
    uid = int(get_jwt_identity())
    u = User.query.get_or_404(uid)
    data = request.get_json() or {}
    try:
        u.lat = float(data.get("lat"))
        u.lon = float(data.get("lon"))
        db.session.commit()
        return jsonify({"ok": True})
    except Exception:
        db.session.rollback()
        return jsonify({"error":"invalid lat/lon"}), 400
