from ..extensions import socketio
from flask_socketio import join_room


@socketio.on("join")
def on_join(data):
    try:
        uid = int(data.get("user_id"))
        join_room(f"user:{uid}")
    except Exception:
        pass


@socketio.on("request_ride")
def on_request_ride(data):
    # kept for future; REST is the primary path
    socketio.emit("ride_update", {"info": "use REST /passenger/request for now"})

