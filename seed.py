from app import create_app, db
from app.models.user import User
from app.utils.geolocation import geocode
import time

app = create_app()

with app.app_context():
    # ⚡ Ajout d’un administrateur par défaut
    admin_address = "125 Rue Watson, Sherbrooke, QC, Canada"
    loc = geocode(admin_address)
    lat, lon = (loc.latitude, loc.longitude) if loc else (None, None)

    admin = User(
        name="Admin",
        phone="14385299073",
        address=admin_address,
        lat=lat,
        lon=lon,
        role="admin",        # rôle administrateur
        has_vehicle=False,
        can_drive=False,
        capacity=0,
        wants_ride=False
    )

    if not User.query.filter_by(phone="14385299073").first():
        db.session.add(admin)
        db.session.commit()
        print("✅ Administrateur créé !")
    else:
        print("ℹ️ Administrateur déjà existant.")

    # ---------------------------
    # 📌 Membres réguliers
    # ---------------------------
    members_data = [
        {"name": "Paul Tremblay", "phone": "15145550001", "address": "1010 Rue Galt Ouest, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 4, "wants_ride": False},
        {"name": "Marie Gagnon", "phone": "15145550002", "address": "40 Rue Belvédère Nord, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
        {"name": "Luc Boucher", "phone": "15145550003", "address": "235 Rue King Ouest, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 3, "wants_ride": False},
        {"name": "Sophie Roy", "phone": "15145550004", "address": "75 Rue Frontenac, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
        {"name": "David Lavoie", "phone": "15145550005", "address": "200 Rue Alexandre, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 4, "wants_ride": False},
        {"name": "Julie Fortin", "phone": "15145550006", "address": "520 Rue Galt Est, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
        {"name": "Mathieu Leblanc", "phone": "15145550007", "address": "1125 Rue King Est, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 2, "wants_ride": False},
        {"name": "Isabelle Côté", "phone": "15145550008", "address": "300 Rue Terrill, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
        {"name": "Jean-François Gagné", "phone": "15145550009", "address": "850 Rue Conseil, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 3, "wants_ride": False},
        {"name": "Caroline Dubé", "phone": "15145550010", "address": "120 Rue Short, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
        # 👉 tu peux continuer à 50 membres en suivant ce format
    ]

    for data in members_data:
        print(f"📍 Géocodage de {data['name']} – {data['address']}")
        loc = geocode(data["address"])
        lat, lon = (loc.latitude, loc.longitude) if loc else (None, None)

        # éviter doublons avec téléphone
        if not User.query.filter_by(phone=data["phone"]).first():
            user = User(
                name=data["name"],
                phone=data["phone"],
                address=data["address"],
                lat=lat,
                lon=lon,
                role="driver" if data["has_vehicle"] else "passenger",
                has_vehicle=data["has_vehicle"],
                can_drive=data["can_drive"],
                capacity=data["capacity"],
                wants_ride=data["wants_ride"]
            )
            db.session.add(user)
            db.session.commit()
            print(f"✅ {data['name']} ajouté.")
            time.sleep(1)  # limite API Nominatim
        else:
            print(f"ℹ️ {data['name']} déjà présent.")

    print("🌱 Insertion des membres terminée avec succès !")
