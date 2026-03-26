import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("METEOFRANCE_API_KEY")
if not API_KEY:
    raise RuntimeError("Clé API absente")

URL = "https://public-api.meteofrance.fr/public/DPClim/v1/liste-stations/quotidienne"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

params = {
    "id-departement": "69"
}

r = requests.get(URL, headers=headers, params=params, timeout=30)

print("Status code :", r.status_code)

if r.status_code == 200:
    stations = r.json()
    print(f"{len(stations)} stations trouvées\n")

    for s in stations:
        print(
            f"{s['id']} | {s['nom']} | "
            f"posteOuvert={s['posteOuvert']} | "
            f"typePoste={s['typePoste']}"
        )
else:
    print("Erreur :", r.text)
