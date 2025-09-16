from ..extensions import socketio, db
from ..models.user import User
from ..models.location import LocationPing
from flask_socketio import join_room


@socketio.on("join")
def on_join(data):
    # data: {user_id, role}
    try:
        uid = int(data.get("user_id"))
        role = data.get("role")
        join_room(f"user:{uid}")
        if role == "driver":
            join_room("drivers")
    except Exception:
        pass


@socketio.on("driver_available")
def on_driver_available(data):
    uid = int(data.get("user_id"))
    available = bool(data.get("available"))
    u = User.query.get(uid)
    if u and u.role == "driver":
        u.is_available = available
        db.session.commit()
        socketio.emit("toast", {"msg": f"Driver {u.name} -> {'ON' if available else 'OFF'}"})


@socketio.on("location_update")
def on_location_update(data):
    uid = int(data.get("user_id"))
    lat = float(data.get("lat"))
    lon = float(data.get("lon"))
    u = User.query.get(uid)
    if not u:
        return
    u.lat, u.lon = lat, lon
    db.session.add(LocationPing(user_id=uid, lat=lat, lon=lon))
    db.session.commit()
    if u.role == "driver":
        socketio.emit("driver_move", {"driver_id": u.id, "lat": lat, "lon": lon})

