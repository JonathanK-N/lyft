from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..extensions import db
from ..models.user import User

bp = Blueprint("auth", __name__)

@bp.post("/register")
def register():
    data = request.get_json() or {}
    required = ["name", "phone", "address", "role", "password"]
    for k in required:
        if k not in data:
            return jsonify({"error": f"missing {k}"}), 400
    u = User(
        name=data["name"].strip(),
        email=(data.get("email") or None),
        phone=data["phone"].strip(),
        whatsapp=data.get("whatsapp") or data["phone"].strip(),
        address=data["address"].strip(),
        role=data["role"],
        has_vehicle=bool(data.get("has_vehicle")),
        capacity=int(data.get("capacity") or 0),
        is_available=False,
    )
    if data.get("password"):
        u.set_password(data["password"])
    try:
        db.session.add(u)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"registration_failed: {str(e)}"}), 500
    token = create_access_token(identity=str(u.id))
    return jsonify({"user_id": u.id, "token": token})

@bp.post("/login")
def login():
    data = request.get_json() or {}
    phone = (data.get("phone") or "").strip()
    password = data.get("password") or ""
    if not phone or not password:
        return jsonify({"error": "missing phone/password"}), 400
    u = User.query.filter_by(phone=phone).first()
    if not u or not u.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401
    token = create_access_token(identity=str(u.id))
    return jsonify({"user_id": u.id, "token": token})

@bp.post("/login-by-id")
def login_by_id():
    data = request.get_json() or {}
    uid = data.get("user_id")
    if not uid: return jsonify({"error":"missing user_id"}), 400
    if not User.query.get(uid): return jsonify({"error":"not found"}), 404
    token = create_access_token(identity=str(uid))
    return jsonify({"token": token})

@bp.get("/me")
@jwt_required()
def me():
    uid = int(get_jwt_identity())
    u = User.query.get_or_404(uid)
    return jsonify({
        "id": u.id,
        "name": u.name,
        "phone": u.phone,
        "email": u.email,
        "role": u.role,
        "capacity": u.capacity,
        "is_available": u.is_available,
    })
