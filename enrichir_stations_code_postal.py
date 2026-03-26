import time
import requests

# Liste des stations météo (extrait, à compléter avec toutes)
stations = [
    {"poste": "01089001", "lat": 45.976500, "lon": 5.329333},
    {"poste": "01269001", "lat": 46.148167, "lon": 5.607333},
    {"poste": "01064001", "lat": 45.777167, "lon": 5.487167},
]

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

HEADERS = {
    "User-Agent": "donnees-meteo/1.0 (contact@entreprise.fr)"
}

def reverse_geocode(lat, lon):
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1
    }

    r = requests.get(
        NOMINATIM_URL,
        params=params,
        headers=HEADERS,
        timeout=20
    )
    r.raise_for_status()

    address = r.json().get("address", {})

    commune = (
        address.get("city")
        or address.get("town")
        or address.get("village")
    )
    code_postal = address.get("postcode")

    return commune, code_postal


print("POSTE;LAT;LON;COMMUNE;CODE_POSTAL")

for s in stations:
    try:
        commune, cp = reverse_geocode(s["lat"], s["lon"])
        print(
            f'{s["poste"]};{s["lat"]};{s["lon"]};{commune};{cp}'
        )
        time.sleep(1)  # respect Nominatim
    except Exception as e:
        print(
            f'{s["poste"]};{s["lat"]};{s["lon"]};;;ERREUR'
        )
