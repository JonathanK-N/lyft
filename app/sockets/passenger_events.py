from ..extensions import socketio

@socketio.on("request_ride")  # si tu veux déclencher via sockets (on l’a aussi en REST)
def on_request_ride(data):
    # tu peux router vers la même logique que /passenger/request si tu veux converger
    socketio.emit("ride_update", {"info": "use REST /passenger/request for now"})
