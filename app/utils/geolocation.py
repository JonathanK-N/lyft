from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Initialisation du géocodeur Nominatim
geolocator = Nominatim(user_agent="lyft_church_app")

def geocode(address):
    """
    Retourne un objet contenant latitude et longitude pour une adresse donnée.
    Exemple d’utilisation :
        loc = geocode("125 Rue King Est, Sherbrooke, QC, Canada")
        if loc:
            print(loc.latitude, loc.longitude)
    """
    try:
        return geolocator.geocode(address)
    except Exception as e:
        print(f"❌ Erreur de géocodage pour {address}: {e}")
        return None

def distance_km(lat1, lon1, lat2, lon2):
    """
    Calcule la distance en kilomètres entre deux points GPS.
    Exemple :
        d = distance_km(45.4, -71.9, 45.5, -71.8)
        print(f"{d:.2f} km")
    """
    try:
        return geodesic((lat1, lon1), (lat2, lon2)).km
    except Exception as e:
        print(f"❌ Erreur de calcul de distance: {e}")
        return None
