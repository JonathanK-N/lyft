from flask import Blueprint, jsonify, request, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.user import User
from ..models.ride import Ride, RidePassenger
from ..utils.geolocation import distance_km

bp = Blueprint("driver", __name__)

@bp.get("/")
def driver_portal_page():
    # Page UI chauffeur (les appels API nécessitent un JWT)
    from ..config import Config
    return render_template("portal_driver.html", church_lat=Config.CHURCH_LAT, church_lon=Config.CHURCH_LON)

@bp.post("/availability")
@jwt_required()
def set_availability():
    uid = int(get_jwt_identity())
    u = User.query.get_or_404(uid)
    if u.role != "driver":
        return jsonify({"error":"not a driver"}), 403
    available = bool((request.get_json() or {}).get("available"))
    u.is_available = available
    db.session.commit()
    return jsonify({"ok": True, "is_available": u.is_available})

@bp.get("/assigned")
@jwt_required()
def assigned():
    uid = int(get_jwt_identity())
    d = User.query.get_or_404(uid)
    if d.role != "driver":
        return jsonify({"error":"not a driver"}), 403
    rides = Ride.query.filter_by(driver_id=d.id).all()
    passenger_ids = [rp.passenger_id for r in rides for rp in RidePassenger.query.filter_by(ride_id=r.id).all()]
    ps = User.query.filter(User.id.in_(passenger_ids)).all()
    out = []
    for p in ps:
        dk = distance_km((d.lat, d.lon), (p.lat, p.lon)) if all([d.lat,d.lon,p.lat,p.lon]) else None
        out.append({"id":p.id, "name":p.name, "phone":p.phone, "whatsapp":p.whatsapp or p.phone, "address":p.address, "distance_km": dk})
    return jsonify(out)
