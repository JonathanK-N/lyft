from flask import Blueprint, render_template, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.user import User
from ..models.ride import Ride, RideRequest, RidePassenger
from ..models.event import Event
from ..extensions import db

bp = Blueprint("admin", __name__)

def is_admin(user_id: int) -> bool:
    u = User.query.get(user_id)
    return bool(u and u.role == "admin")

@bp.get("/dashboard")
def admin_page():
    # Le template charge les données via API protégées (JWT admin)
    return render_template("admin_dashboard.html")

@bp.post("/toggle-driver")
@jwt_required()
def toggle_driver():
    admin_id = int(get_jwt_identity())
    if not is_admin(admin_id):
        return jsonify({"error": "forbidden"}), 403
    uid = request.json.get("user_id")
    u = User.query.get_or_404(uid)
    u.role = "driver" if u.role != "driver" else "passenger"
    db.session.commit()
    return jsonify({"ok": True, "role": u.role})

@bp.post("/set-availability")
@jwt_required()
def set_availability():
    admin_id = int(get_jwt_identity())
    if not is_admin(admin_id):
        return jsonify({"error": "forbidden"}), 403
    uid = request.json.get("user_id")
    available = bool(request.json.get("available"))
    u = User.query.get_or_404(uid)
    u.is_available = available
    db.session.commit()
    return jsonify({"ok": True, "is_available": u.is_available})

# -------- Members management --------
@bp.get("/users")
@jwt_required()
def list_users():
    admin_id = int(get_jwt_identity())
    if not is_admin(admin_id):
        return jsonify({"error": "forbidden"}), 403
    users = User.query.all()
    return jsonify([
        {"id":u.id, "name":u.name, "phone":u.phone, "role":u.role, "capacity":u.capacity, "is_available":u.is_available}
        for u in users
    ])

@bp.post("/set-role")
@jwt_required()
def set_role():
    admin_id = int(get_jwt_identity())
    if not is_admin(admin_id):
        return jsonify({"error": "forbidden"}), 403
    uid = int(request.json.get("user_id"))
    role = request.json.get("role")
    if role not in ("admin","driver","passenger"):
        return jsonify({"error":"invalid role"}), 400
    u = User.query.get_or_404(uid)
    u.role = role
    db.session.commit()
    return jsonify({"ok": True, "role": u.role})

@bp.post("/update-user")
@jwt_required()
def update_user():
    admin_id = int(get_jwt_identity())
    if not is_admin(admin_id):
        return jsonify({"error": "forbidden"}), 403
    uid = int(request.json.get("user_id"))
    capacity = request.json.get("capacity")
    is_available = request.json.get("is_available")
    u = User.query.get_or_404(uid)
    if capacity is not None:
        u.capacity = int(capacity)
    if is_available is not None:
        u.is_available = bool(is_available)
    db.session.commit()
    return jsonify({"ok": True})

# -------- Events management --------
@bp.get("/events")
@jwt_required()
def events_list():
    admin_id = int(get_jwt_identity())
    if not is_admin(admin_id):
        return jsonify({"error": "forbidden"}), 403
    events = Event.query.order_by(Event.start_at.desc()).all()
    return jsonify([
        {"id":e.id, "title":e.title, "description":e.description, "start_at": e.start_at.isoformat(), "location":e.location}
        for e in events
    ])

@bp.post("/events")
@jwt_required()
def events_create():
    admin_id = int(get_jwt_identity())
    if not is_admin(admin_id):
        return jsonify({"error": "forbidden"}), 403
    data = request.get_json() or {}
    from datetime import datetime
    try:
        start_at = datetime.fromisoformat(data.get("start_at"))
    except Exception:
        return jsonify({"error":"invalid start_at"}), 400
    e = Event(title=data.get("title","Sans titre"), description=data.get("description"), start_at=start_at, location=data.get("location"), lat=data.get("lat"), lon=data.get("lon"))
    db.session.add(e); db.session.commit()
    return jsonify({"ok": True, "id": e.id})

@bp.delete("/events/<int:event_id>")
@jwt_required()
def events_delete(event_id:int):
    admin_id = int(get_jwt_identity())
    if not is_admin(admin_id):
        return jsonify({"error": "forbidden"}), 403
    e = Event.query.get_or_404(event_id)
    db.session.delete(e); db.session.commit()
    return jsonify({"ok": True})
