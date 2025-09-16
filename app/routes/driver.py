from flask import Blueprint, jsonify, request, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db, socketio
from ..models.user import User
from ..models.ride import Ride, RidePassenger, RideRequest
from ..utils.geolocation import distance_km
from ..config import Config

bp = Blueprint("driver", __name__)

@bp.get("/")
def driver_portal_page():
    # Page UI chauffeur (les appels API nécessitent un JWT)
    return render_template("portal_driver.html", church_lat=Config.CHURCH_LAT, church_lon=Config.CHURCH_LON)


@bp.post("/location")
@jwt_required()
def update_location():
    uid = int(get_jwt_identity())
    d = User.query.get_or_404(uid)
    data = request.get_json() or {}
    try:
        d.lat = float(data.get("lat"))
        d.lon = float(data.get("lon"))
        db.session.commit()
        return jsonify({"ok": True})
    except Exception:
        db.session.rollback()
        return jsonify({"error":"invalid lat/lon"}), 400


@bp.get("/requests")
@jwt_required()
def list_requests():
    uid = int(get_jwt_identity())
    d = User.query.get_or_404(uid)
    if d.role != "driver":
        return jsonify({"error":"not a driver"}), 403
    radius = float(request.args.get("radius_km") or 0)
    reqs = RideRequest.query.filter_by(status="pending").all()
    out = []
    for rr in reqs:
        p = User.query.get(rr.passenger_id)
        if not p:
            continue
        plat, plon = rr.pickup_lat or p.lat, rr.pickup_lon or p.lon
        d_to_p = distance_km((d.lat, d.lon), (plat, plon)) if all([d.lat, d.lon, plat, plon]) else None
        p_to_church = distance_km((plat, plon), (Config.CHURCH_LAT, Config.CHURCH_LON)) if all([plat, plon]) else None
        if radius and (d_to_p is None or d_to_p > radius):
            continue
        out.append({
            "request_id": rr.id,
            "passenger": {"id": p.id, "name": p.name, "phone": p.phone, "whatsapp": p.whatsapp or p.phone},
            "pickup": {"lat": plat, "lon": plon},
            "distance_to_passenger_km": d_to_p,
            "distance_to_church_km": p_to_church,
            "created_at": rr.created_at.isoformat(),
        })
    out.sort(key=lambda x: (x["distance_to_passenger_km"] if x["distance_to_passenger_km"] is not None else 1e9))
    return jsonify(out)


@bp.post("/accept")
@jwt_required()
def accept_request():
    uid = int(get_jwt_identity())
    d = User.query.get_or_404(uid)
    if d.role != "driver":
        return jsonify({"error":"not a driver"}), 403
    data = request.get_json() or {}
    rid = data.get("request_id")
    rr = RideRequest.query.get_or_404(rid)
    if rr.status != "pending":
        return jsonify({"error":"request not pending"}), 400
    if (d.capacity or 0) <= 0:
        return jsonify({"error":"driver has no capacity"}), 400
    # assign
    ride = Ride(driver_id=d.id, status="assigned")
    db.session.add(ride); db.session.flush()
    db.session.add(RidePassenger(ride_id=ride.id, passenger_id=rr.passenger_id))
    d.capacity = max(0, (d.capacity or 0) - 1)
    rr.status = "assigned"; rr.assigned_driver_id = d.id
    db.session.commit()
    p = User.query.get(rr.passenger_id)
    plat, plon = rr.pickup_lat or p.lat, rr.pickup_lon or p.lon
    d_to_p = distance_km((d.lat, d.lon), (plat, plon)) if all([d.lat, d.lon, plat, plon]) else None
    p_to_church = distance_km((plat, plon), (Config.CHURCH_LAT, Config.CHURCH_LON)) if all([plat, plon]) else None
    # Notifie le passager et les chauffeurs
    socketio.emit("request:accepted", {"request_id": rr.id, "passenger_id": p.id, "driver": {"id": d.id, "name": d.name, "phone": d.phone}})
    return jsonify({
        "ok": True,
        "ride_id": ride.id,
        "passenger": {"id": p.id, "name": p.name, "phone": p.phone, "whatsapp": p.whatsapp or p.phone},
        "distance_to_passenger_km": d_to_p,
        "distance_to_church_km": p_to_church,
    })

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
