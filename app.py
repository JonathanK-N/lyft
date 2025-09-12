import math
from datetime import datetime
from typing import List, Tuple, Dict, Optional

from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.distance import geodesic

# OR-Tools (optionnel)
try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    ORTOOLS_AVAILABLE = True
except Exception:
    ORTOOLS_AVAILABLE = False

# ----------------------------
# CONFIG
# ----------------------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///church_lyft.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Adresse de l'église (libellé) — à personnaliser
EGLISE_ADRESSE = "350 Rue King O, Sherbrooke, QC, Canada"
# User agent OSM (obligatoire). Mets idéalement le nom de ton app + contact.
GEOCODER = Nominatim(user_agent="church-lyft-app/1.1 (contact@example.com)")
geocode = RateLimiter(GEOCODER.geocode, min_delay_seconds=1.0)  # Respect policy OSM

# ----------------------------
# MODELES
# ----------------------------
class Member(db.Model):
    __tablename__ = "members"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

    # Adresse textuelle + coords géocodées
    address = db.Column(db.String(255), nullable=False)
    lat = db.Column(db.Float, nullable=True)
    lon = db.Column(db.Float, nullable=True)

    # Rôles & capacités
    has_vehicle = db.Column(db.Boolean, default=False)       # possède une auto
    can_drive = db.Column(db.Boolean, default=False)         # volontaire pour conduire
    capacity = db.Column(db.Integer, default=0)              # nb passagers max (hors conducteur)
    wants_ride = db.Column(db.Boolean, default=False)        # a besoin d'un lyft

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Ride(db.Model):
    __tablename__ = "rides"
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    service_time = db.Column(db.DateTime, nullable=False)  # <-- NOUVEAU

    driver = db.relationship("Member", backref="rides")

class RideStop(db.Model):
    """
    Itinéraire d'un trajet (ordre des arrêts).
    On enregistre deux séquences:
      - 'direction' = 'to_church' (ramassage -> église)
      - 'direction' = 'from_church' (église -> déposes)
    """
    __tablename__ = "ride_stops"
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey("rides.id"), nullable=False)
    passenger_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    order_index = db.Column(db.Integer, nullable=False)
    direction = db.Column(db.String(20), nullable=False)  # 'to_church' | 'from_church'

    ride = db.relationship("Ride", backref="stops")
    passenger = db.relationship("Member")

# ----------------------------
# OUTILS GEO
# ----------------------------
def ensure_geocoded(address: str) -> Tuple[float, float]:
    """
    Géocode une adresse texte -> (lat, lon).
    Lève ValueError si introuvable.
    """
    loc = geocode(address)
    if not loc:
        raise ValueError(f"Adresse introuvable: {address}")
    return (loc.latitude, loc.longitude)

def distance_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return geodesic(a, b).km

# Heuristique basique
def nearest_neighbor_order(start: Tuple[float, float], points: List[Tuple[int, Tuple[float, float]]]) -> List[int]:
    remaining = points[:]
    order = []
    current = start
    while remaining:
        best_i, best_d = 0, float("inf")
        for i, (_, coords) in enumerate(remaining):
            d = distance_km(current, coords)
            if d < best_d:
                best_d = d
                best_i = i
        pid, coords = remaining.pop(best_i)
        order.append(pid)
        current = coords
    return order

# OR-Tools TSP avec départ/arrivée imposés (si disponible)
def ortools_tsp_fixed_endpoints(start: Tuple[float, float],
                                end: Tuple[float, float],
                                points: List[Tuple[int, Tuple[float, float]]]) -> Optional[List[int]]:
    if not ORTOOLS_AVAILABLE or not points:
        return None

    # Construire liste de tous les noeuds: start, points..., end
    all_nodes = [("start", start)] + points + [("end", end)]
    n = len(all_nodes)

    # Matrice des distances (entiers en mètres)
    def dist(i, j):
        return int(round(geodesic(all_nodes[i][1], all_nodes[j][1]).m * 1.0))

    dist_matrix = [[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                dist_matrix[i][j] = dist(i, j)

    # Routing
    manager = pywrapcp.RoutingIndexManager(n, 1, 0, n-1)  # 1 véhicule, start=0, end=n-1
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        a = manager.IndexToNode(from_index)
        b = manager.IndexToNode(to_index)
        return dist_matrix[a][b]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Paramètres
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.FromSeconds(3)

    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        return None

    # Extraire ordre: on ignore le "start" et "end"
    index = routing.Start(0)
    order_ids = []
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        if 1 <= node <= len(points):  # nodes 1..len(points) => passagers
            pass_id = points[node-1][0]
            order_ids.append(pass_id)
        index = solution.Value(routing.NextVar(index))
    return order_ids

# ----------------------------
# INIT DB & EGLISE COORDS
# ----------------------------
with app.app_context():
    db.create_all()
    EGLISE_COORDS = ensure_geocoded(EGLISE_ADRESSE)

# ----------------------------
# HELPERS ASSIGNATION
# ----------------------------
def assign_passengers_to_drivers(drivers: List['Member'], passengers: List['Member']) -> Dict[int, List['Member']]:
    """
    Attribution gourmande par capacité:
      - Trie les passagers (plus proches de l’église d’abord => favorise les grappes)
      - Pour chaque passager, choisit le conducteur le plus proche qui a encore de la capacité
    """
    capacity_left = {d.id: max(0, int(d.capacity or 0)) for d in drivers}
    passengers_sorted = sorted(passengers, key=lambda p: distance_km((p.lat, p.lon), EGLISE_COORDS))
    buckets: Dict[int, List[Member]] = {d.id: [] for d in drivers}

    for p in passengers_sorted:
        best_driver = None
        best_dist = float("inf")
        ppos = (p.lat, p.lon)
        for d in drivers:
            if capacity_left[d.id] <= 0:
                continue
            dpos = (d.lat, d.lon)
            dcp = distance_km(dpos, ppos)
            if dcp < best_dist:
                best_dist = dcp
                best_driver = d
        if best_driver:
            buckets[best_driver.id].append(p)
            capacity_left[best_driver.id] -= 1
    return buckets

def plan_routes_for_driver(driver: 'Member', passengers: List['Member']) -> Dict[str, List[int]]:
    """
    Calcule deux séquences d'arrêts:
      - to_church: driver -> [pickups...] -> church
      - from_church: church -> [dropoffs...] -> driver
    Essaie OR-Tools, sinon heuristique plus proche voisin.
    """
    dpos = (driver.lat, driver.lon)
    pts = [(p.id, (p.lat, p.lon)) for p in passengers]

    # Aller (vers église)
    if ORTOOLS_AVAILABLE:
        order_to = ortools_tsp_fixed_endpoints(dpos, EGLISE_COORDS, pts)
    else:
        order_to = None
    if not order_to:
        order_to = nearest_neighbor_order(dpos, pts)

    # Retour (depuis église, dépôt des mêmes domiciles) + retour conducteur chez lui
    # Pour l'ordre, on ignore la dernière étape "retour chez le driver" (calcul distance séparément)
    if ORTOOLS_AVAILABLE:
        order_from = ortools_tsp_fixed_endpoints(EGLISE_COORDS, dpos, pts)
    else:
        order_from = None
    if not order_from:
        order_from = nearest_neighbor_order(EGLISE_COORDS, pts)

    return {"to_church": order_to, "from_church": order_from}

# ----------------------------
# API MEMBRES
# ----------------------------
@app.route("/members", methods=["POST"])
def add_member():
    """
    Inscription / mise à jour d'un membre.
    JSON attendu:
    {
      "name": "Jean",
      "address": "123 Rue ...",
      "has_vehicle": true,
      "can_drive": true,
      "capacity": 4,            # nombre de passagers max
      "wants_ride": false
    }
    """
    data = request.json or {}
    required = ["name", "address"]
    for k in required:
        if k not in data:
            return jsonify({"error": f"Champ requis manquant: {k}"}), 400

    try:
        lat, lon = ensure_geocoded(data["address"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    m = Member(
        name=data["name"],
        address=data["address"],
        lat=lat,
        lon=lon,
        has_vehicle=bool(data.get("has_vehicle", False)),
        can_drive=bool(data.get("can_drive", False)),
        capacity=int(data.get("capacity", 0) or 0),
        wants_ride=bool(data.get("wants_ride", False)),
    )
    db.session.add(m)
    db.session.commit()
    return jsonify({"message": "Membre enregistré", "member_id": m.id})

@app.route("/members", methods=["GET"])
def list_members():
    rows = Member.query.order_by(Member.created_at.desc()).all()
    out = []
    for m in rows:
        out.append({
            "id": m.id,
            "name": m.name,
            "address": m.address,
            "lat": m.lat, "lon": m.lon,
            "has_vehicle": m.has_vehicle, "can_drive": m.can_drive,
            "capacity": m.capacity, "wants_ride": m.wants_ride,
        })
    return jsonify(out)

# ----------------------------
# API ATRRIBUTION & TRAJETS (avec service_time)
# ----------------------------
@app.route("/assign", methods=["POST"])
def assign_now():
    """
    Lance une attribution + planification d'itinéraires pour un 'service_time' (ISO 8601).
    JSON:
    {
      "service_time": "2025-09-15T10:00:00"
    }
    """
    data = request.json or {}
    st = data.get("service_time")
    if not st:
        return jsonify({"error": "Champ requis 'service_time' (ISO 8601)"}), 400

    try:
        service_time = datetime.fromisoformat(st)
    except Exception:
        return jsonify({"error": "Format 'service_time' invalide (ISO 8601 attendu)"}), 400

    drivers: List[Member] = Member.query.filter_by(can_drive=True).all()
    drivers = [d for d in drivers if d.lat is not None and d.lon is not None and (d.capacity or 0) > 0]

    passengers: List[Member] = Member.query.filter_by(wants_ride=True).all()
    passengers = [p for p in passengers if p.lat is not None and p.lon is not None]

    if not drivers or not passengers:
        return jsonify({"message": "Aucun conducteur ou aucun passager prêt à attribuer.", "drivers": len(drivers), "passengers": len(passengers)})

    buckets = assign_passengers_to_drivers(drivers, passengers)

    results = []
    for d in drivers:
        assigned = buckets.get(d.id, [])
        if not assigned:
            continue

        ride = Ride(driver_id=d.id, service_time=service_time)
        db.session.add(ride)
        db.session.flush()  # pour ride.id

        plan = plan_routes_for_driver(d, assigned)

        # Enregistrer l'ordre des stops
        for idx, pid in enumerate(plan["to_church"]):
            db.session.add(RideStop(ride_id=ride.id, passenger_id=pid, order_index=idx, direction="to_church"))
        for idx, pid in enumerate(plan["from_church"]):
            db.session.add(RideStop(ride_id=ride.id, passenger_id=pid, order_index=idx, direction="from_church"))

        # Estimation des distances (aller + retour)
        dpos = (d.lat, d.lon)
        pickups_coords = [(Member.query.get(pid).lat, Member.query.get(pid).lon) for pid in plan["to_church"]]
        dist_aller = 0.0
        cur = dpos
        for c in pickups_coords:
            dist_aller += distance_km(cur, c)
            cur = c
        dist_aller += distance_km(cur, EGLISE_COORDS)

        drop_coords = [(Member.query.get(pid).lat, Member.query.get(pid).lon) for pid in plan["from_church"]]
        dist_retour = 0.0
        cur = EGLISE_COORDS
        for c in drop_coords:
            dist_retour += distance_km(cur, c)
            cur = c
        # Retour conducteur chez lui
        dist_retour += distance_km(cur, dpos)

        results.append({
            "ride_id": ride.id,
            "driver": {"id": d.id, "name": d.name, "capacity": d.capacity, "start": {"lat": d.lat, "lon": d.lon}},
            "passengers": [{"id": p.id, "name": p.name} for p in assigned],
            "order_to_church": plan["to_church"],
            "order_from_church": plan["from_church"],
            "distance_km_estimated": round(dist_aller + dist_retour, 2),
            "distance_split": {"aller": round(dist_aller, 2), "retour": round(dist_retour, 2)}
        })

    db.session.commit()
    return jsonify({
        "church": {"address": EGLISE_ADRESSE, "lat": EGLISE_COORDS[0], "lon": EGLISE_COORDS[1]},
        "service_time": service_time.isoformat(),
        "rides": results,
        "optimizer": "ortools" if ORTOOLS_AVAILABLE else "nearest_neighbor"
    })

@app.route("/api/rides", methods=["GET"])
def api_rides_by_service_time():
    """
    Retourne les trajets (avec arrêts) pour un service_time (ISO 8601 exact).
    GET /api/rides?service_time=2025-09-15T10:00:00
    """
    st = request.args.get("service_time")
    if not st:
        return jsonify({"error": "Paramètre 'service_time' requis"}), 400
    try:
        service_time = datetime.fromisoformat(st)
    except Exception:
        return jsonify({"error": "Format 'service_time' invalide"}), 400

    rides = Ride.query.filter(Ride.service_time == service_time).all()
    out = []
    for r in rides:
        d = r.driver
        stops_to = sorted([s for s in r.stops if s.direction == "to_church"], key=lambda s: s.order_index)
        stops_from = sorted([s for s in r.stops if s.direction == "from_church"], key=lambda s: s.order_index)
        out.append({
            "ride_id": r.id,
            "driver": {"id": d.id, "name": d.name, "lat": d.lat, "lon": d.lon},
            "to_church": [{
                "order": s.order_index,
                "passenger_id": s.passenger_id,
                "name": s.passenger.name,
                "lat": s.passenger.lat,
                "lon": s.passenger.lon
            } for s in stops_to],
            "from_church": [{
                "order": s.order_index,
                "passenger_id": s.passenger_id,
                "name": s.passenger.name,
                "lat": s.passenger.lat,
                "lon": s.passenger.lon
            } for s in stops_from],
        })
    return jsonify({
        "church": {"address": EGLISE_ADRESSE, "lat": EGLISE_COORDS[0], "lon": EGLISE_COORDS[1]},
        "service_time": service_time.isoformat(),
        "rides": out
    })

# ----------------------------
# FRONT LEAFLET (minimal)
# ----------------------------
MAP_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Church Lyft – Carte</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
    crossorigin=""
  />
  <style>
    html, body, #map { height: 100%; margin: 0; }
    .card {
      position: absolute; top: 10px; left: 10px; background: #fff;
      padding: 10px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,.15);
      z-index: 1000; max-width: 360px; font-family: system-ui, sans-serif;
    }
    .badge { display:inline-block; padding:2px 6px; border-radius:6px; background:#eee; margin-left:6px; font-size:12px; }
    .driver { font-weight: 600; margin-top: 8px; }
    .hint { font-size: 12px; color: #555; margin-top: 6px; }
  </style>
</head>
<body>
  <div class="card">
    <div><strong>Visualisation des trajets</strong></div>
    <div class="hint">Passer <code>?service_time=YYYY-MM-DDTHH:MM:SS</code> dans l’URL</div>
    <div class="hint">Ex.: <code>?service_time=2025-09-15T10:00:00</code></div>
    <div id="summary" class="hint"></div>
  </div>
  <div id="map"></div>

  <script
    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
    crossorigin=""
  ></script>
  <script>
    function getQueryParam(name) {
      const url = new URL(window.location.href);
      return url.searchParams.get(name);
    }

    const map = L.map('map').setView([45.4, -71.9], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    const st = getQueryParam('service_time');
    if (!st) {
      document.getElementById('summary').innerText = "Ajoute ?service_time=... à l’URL pour charger les trajets.";
    } else {
      fetch(`/api/rides?service_time=${encodeURIComponent(st)}`)
        .then(r => r.json())
        .then(data => {
          const church = [data.church.lat, data.church.lon];
          const churchIcon = L.icon({
            iconUrl: 'https://cdn-icons-png.flaticon.com/512/3178/3178321.png',
            iconSize: [28, 28]
          });
          L.marker(church, {icon: churchIcon}).addTo(map).bindPopup("Église");

          const colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"];
          let bounds = L.latLngBounds(church, church);
          const rides = data.rides || [];
          document.getElementById('summary').innerText = `${rides.length} trajet(s) trouvé(s) — ${data.service_time}`;

          rides.forEach((ride, idx) => {
            const color = colors[idx % colors.length];
            const driver = [ride.driver.lat, ride.driver.lon];

            // Driver marker
            const dm = L.circleMarker(driver, {radius: 6, weight: 2, color: color, fillOpacity: 0.6}).addTo(map)
              .bindPopup(`<div class="driver">Conducteur: ${ride.driver.name}</div>`);

            bounds.extend(driver);

            // TO CHURCH polyline
            let lineTo = [driver];
            ride.to_church.forEach(s => {
              const p = [s.lat, s.lon];
              lineTo.push(p);
              bounds.extend(p);
              L.circleMarker(p, {radius:4, weight:1, color: color, fillOpacity: 0.9})
                .addTo(map).bindPopup(`Pickup: ${s.name}`);
            });
            lineTo.push(church);
            L.polyline(lineTo, {weight: 3, color: color}).addTo(map).bindPopup(`Aller (driver: ${ride.driver.name})`);

            // FROM CHURCH polyline
            let lineFrom = [church];
            ride.from_church.forEach(s => {
              const p = [s.lat, s.lon];
              lineFrom.push(p);
            });
            lineFrom.push(driver);
            L.polyline(lineFrom, {weight: 2, dashArray: '6,6', color: color}).addTo(map).bindPopup(`Retour (driver: ${ride.driver.name})`);
          });

          map.fitBounds(bounds.pad(0.15));
        })
        .catch(err => {
          document.getElementById('summary').innerText = "Erreur de chargement: " + err;
        });
    }
  </script>
</body>
</html>
"""

@app.route("/map", methods=["GET"])
def map_view():
    # Page Leaflet minimaliste
    return render_template_string(MAP_HTML)

# ----------------------------
# LANCEMENT
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
