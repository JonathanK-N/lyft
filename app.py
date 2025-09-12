from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.distance import geodesic
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///church_lyft.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Géocodeur
geolocator = Nominatim(user_agent="church-lyft-app")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# Coordonnées fixes de l’église (exemple Sherbrooke)
EGLISE_COORDS = (45.4042, -71.8929)

# ----------------------------
# MODELES
# ----------------------------
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    lat = db.Column(db.Float, nullable=True)
    lon = db.Column(db.Float, nullable=True)
    has_vehicle = db.Column(db.Boolean, default=False)
    can_drive = db.Column(db.Boolean, default=False)
    capacity = db.Column(db.Integer, default=0)
    wants_ride = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()

# ----------------------------
# ROUTES
# ----------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    """Page d’accueil : inscription"""
    if request.method == "POST":
        name = request.form["name"]
        address = request.form["address"]
        has_vehicle = "has_vehicle" in request.form
        can_drive = "can_drive" in request.form
        capacity = int(request.form["capacity"] or 0)
        wants_ride = "wants_ride" in request.form

        # Géocodage
        loc = geocode(address)
        lat, lon = (loc.latitude, loc.longitude) if loc else (None, None)

        m = Member(
            name=name,
            address=address,
            lat=lat,
            lon=lon,
            has_vehicle=has_vehicle,
            can_drive=can_drive,
            capacity=capacity,
            wants_ride=wants_ride
        )
        db.session.add(m)
        db.session.commit()
        return redirect(url_for("index"))

    membres = Member.query.all()
    return render_template("index.html", membres=membres)


@app.route("/driver/<int:member_id>")
def driver_view(member_id):
    """Interface conducteur : voir ses passagers attribués"""
    driver = Member.query.get_or_404(member_id)
    if not driver.can_drive:
        return "Ce membre n’est pas un conducteur.", 400

    # Passagers proches
    passengers = Member.query.filter_by(wants_ride=True).all()
    assigned = []
    for p in passengers:
        if p.lat and p.lon and driver.lat and driver.lon:
            dist = geodesic((driver.lat, driver.lon), (p.lat, p.lon)).km
            if dist < 5:  # par ex. <= 5 km autour
                assigned.append((p, round(dist, 2)))

    return render_template("driver.html", driver=driver, assigned=assigned)


@app.route("/passenger/<int:member_id>")
def passenger_view(member_id):
    """Interface passager : voir son conducteur attribué"""
    passenger = Member.query.get_or_404(member_id)
    if not passenger.wants_ride:
        return "Ce membre n’est pas un passager.", 400

    # Trouver conducteur le plus proche
    drivers = Member.query.filter_by(can_drive=True).all()
    best_driver, best_dist = None, float("inf")
    for d in drivers:
        if d.lat and d.lon and passenger.lat and passenger.lon:
            dist = geodesic((d.lat, d.lon), (passenger.lat, passenger.lon)).km
            if dist < best_dist:
                best_driver, best_dist = d, dist

    return render_template("passenger.html", passenger=passenger,
                           driver=best_driver, distance=round(best_dist, 2) if best_driver else None)


if __name__ == "__main__":
    app.run(debug=True)
