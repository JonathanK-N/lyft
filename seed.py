
from app import app, db, Member, geocode
import time

# --- Liste des membres (copiée du JSON) ---
members_data = [
  {"name": "Paul Tremblay", "address": "1010 Rue Galt Ouest, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 4, "wants_ride": False},
  {"name": "Marie Gagnon", "address": "40 Rue Belvédère Nord, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Luc Boucher", "address": "235 Rue King Ouest, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 3, "wants_ride": False},
  {"name": "Sophie Roy", "address": "75 Rue Frontenac, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Jean-Philippe Côté", "address": "920 Rue du Conseil, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 5, "wants_ride": False},
  {"name": "Isabelle Morin", "address": "12 Rue Marquette, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Marc Lavoie", "address": "400 Rue Dufferin, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 2, "wants_ride": False},
  {"name": "Caroline Fortin", "address": "88 Rue Alexandre, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "David Bouchard", "address": "15 Rue Brooks, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 4, "wants_ride": False},
  {"name": "Julie Gendron", "address": "30 Rue Albert, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},

  {"name": "André Leblanc", "address": "245 Rue Montréal, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 3, "wants_ride": False},
  {"name": "Nathalie Cormier", "address": "66 Rue Terrill, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Pierre Gosselin", "address": "480 Rue Queen, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 4, "wants_ride": False},
  {"name": "Catherine Dubé", "address": "100 Rue McManamy, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Hugo Létourneau", "address": "55 Rue Bowen Sud, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 2, "wants_ride": False},
  {"name": "Valérie Martel", "address": "72 Rue King Est, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Olivier Lapointe", "address": "99 Rue Peel, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 5, "wants_ride": False},
  {"name": "Manon Desjardins", "address": "250 Rue Belvédère Sud, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Éric Côté", "address": "320 Rue Wellington Nord, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 3, "wants_ride": False},
  {"name": "Chantal Moreau", "address": "61 Rue du Parc, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},

  {"name": "Alexandre Simard", "address": "140 Rue Short, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 4, "wants_ride": False},
  {"name": "Émilie Girard", "address": "210 Rue Champlain, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Louis Tremblay", "address": "520 Rue King Est, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 3, "wants_ride": False},
  {"name": "Sarah Gauthier", "address": "180 Rue Alexandre, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Patrick Bérubé", "address": "630 Rue Wellington Sud, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 5, "wants_ride": False},
  {"name": "Amélie Caron", "address": "20 Rue William, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "François Martineau", "address": "88 Rue Terrill, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 4, "wants_ride": False},
  {"name": "Véronique Lavoie", "address": "35 Rue Bank, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Daniel Lefebvre", "address": "122 Rue du Prince, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 2, "wants_ride": False},
  {"name": "Geneviève Pelletier", "address": "300 Rue du Moulin, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},

  {"name": "Michel Côté", "address": "15 Rue du Dépôt, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 3, "wants_ride": False},
  {"name": "Josée Fournier", "address": "99 Rue Saint-François Nord, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Martin Plante", "address": "44 Rue du Lac, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 4, "wants_ride": False},
  {"name": "Stéphanie Dubois", "address": "18 Rue Calixa-Lavallée, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Simon Blais", "address": "72 Rue Bowen Nord, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 5, "wants_ride": False},
  {"name": "Julie Bélanger", "address": "25 Rue Hutchison, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Claude Pelletier", "address": "101 Rue du Conseil, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 2, "wants_ride": False},
  {"name": "Annie Gosselin", "address": "66 Rue Dufferin, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Dominic Gagné", "address": "20 Rue des Quatre-Saisons, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 3, "wants_ride": False},
  {"name": "Mélanie Boucher", "address": "77 Rue Bowen Ouest, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},

  {"name": "Pascal Renaud", "address": "200 Rue Saint-Michel, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 4, "wants_ride": False},
  {"name": "Karine Giroux", "address": "58 Rue Frontenac, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Mathieu Desrosiers", "address": "88 Rue Champlain, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 2, "wants_ride": False},
  {"name": "Isabelle Lebrun", "address": "150 Rue du Conseil, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True},
  {"name": "Philippe Carpentier", "address": "310 Rue William, Sherbrooke, QC, Canada", "has_vehicle": True, "can_drive": True, "capacity": 5, "wants_ride": False},
  {"name": "Sandra Cloutier", "address": "60 Rue Albert, Sherbrooke, QC, Canada", "has_vehicle": False, "can_drive": False, "capacity": 0, "wants_ride": True}
]


# --- Script d’insertion ---
with app.app_context():
    for data in members_data:
        print(f"Géocodage de {data['name']} – {data['address']}")
        loc = geocode(data["address"])
        lat, lon = (loc.latitude, loc.longitude) if loc else (None, None)

        m = Member(
            name=data["name"],
            address=data["address"],
            lat=lat,
            lon=lon,
            has_vehicle=data["has_vehicle"],
            can_drive=data["can_drive"],
            capacity=data["capacity"],
            wants_ride=data["wants_ride"]
        )
        db.session.add(m)
        db.session.commit()

        # ⚠️ Pause pour respecter la limite de Nominatim
        time.sleep(1)

print("✅ Insertion terminée avec succès !")