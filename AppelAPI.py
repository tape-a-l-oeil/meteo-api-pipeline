import os
import time
import requests
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("METEOFRANCE_API_KEY")
if not API_KEY:
    raise RuntimeError("Cle API absente")

URL_COMMANDE = "https://public-api.meteofrance.fr/public/DPClim/v1/commande-station/quotidienne"
URL_DOWNLOAD = "https://public-api.meteofrance.fr/public/DPClim/v1/commande/fichier"

stations_nord = [
    "59343001",
    "59178001",
    "59392001",
    "59512001",
    "59606004",
    "59647001",
    "59183001",
]

target_date = (date.today() - timedelta(days=1)).isoformat()

headers_json = {
    "apikey": API_KEY,
    "Accept": "application/json"
}

headers_csv = {
    "apikey": API_KEY,
    "Accept": "text/csv"
}

os.makedirs("csv", exist_ok=True)

wait_between_stations = 1
wait_before_download = 2
wait_retry_commande = 2
wait_retry_download = 2

stations_ok = []
stations_ko = []

def extraire_id_commande(payload):
    if "elaboreProduitAvecDemandeResponse" in payload:
        return payload["elaboreProduitAvecDemandeResponse"].get("return")
    return (
        payload.get("idCommande")
        or payload.get("id_commande")
        or payload.get("idCmde")
    )

for station_id in stations_nord:
    print(f"\n--- Station {station_id} ---")
    time.sleep(wait_between_stations)

    id_commande = None

    for attempt in range(1, 4):
        print(f"Commande tentative {attempt}/3")

        params = {
            "id-station": station_id,
            "date-deb-periode": f"{target_date}T00:00:00Z",
            "date-fin-periode": f"{target_date}T23:59:59Z"
        }

        try:
            r = requests.get(URL_COMMANDE, headers=headers_json, params=params, timeout=30)
        except requests.RequestException as e:
            print(f"Erreur reseau commande - {e}")
            time.sleep(wait_retry_commande)
            continue

        if r.status_code == 202:
            try:
                payload = r.json()
            except ValueError:
                print(f"Reponse JSON invalide - {r.text}")
                time.sleep(wait_retry_commande)
                continue

            id_commande = extraire_id_commande(payload)

            if id_commande:
                print(f"id_commande = {id_commande}")
                break
            else:
                print(f"id_commande introuvable - payload : {payload}")
                time.sleep(wait_retry_commande)

        elif r.status_code == 500:
            print("Erreur commande - 500 - API instable")
            time.sleep(wait_retry_commande)

        else:
            print(f"Erreur commande - {r.status_code} - {r.text}")
            time.sleep(wait_retry_commande)

    if not id_commande:
        print(f"Echec commande station {station_id}")
        stations_ko.append(station_id)
        continue

    time.sleep(wait_before_download)

    downloaded = False

    for attempt in range(1, 6):
        print(f"Download tentative {attempt}/5")

        params_dl = {"id-cmde": id_commande}

        try:
            r_dl = requests.get(URL_DOWNLOAD, headers=headers_csv, params=params_dl, timeout=60)
        except requests.RequestException as e:
            print(f"Erreur reseau download - {e}")
            time.sleep(wait_retry_download)
            continue

        if r_dl.status_code == 201:
            filepath = f"csv/meteo_{station_id}_{target_date}.csv"
            with open(filepath, "wb") as f:
                f.write(r_dl.content)

            print(f"CSV OK : {filepath}")
            downloaded = True
            stations_ok.append(station_id)
            break

        elif r_dl.status_code == 204:
            print("Fichier en cours de generation")
            time.sleep(wait_retry_download)

        elif r_dl.status_code == 404:
            print("Pas de donnees pour cette periode")
            break

        elif r_dl.status_code == 500:
            print("Erreur download - 500 - API instable")
            time.sleep(wait_retry_download)

        else:
            print(f"Erreur download - {r_dl.status_code} - {r_dl.text}")
            break

    if not downloaded:
        print(f"Echec download station {station_id}")
        stations_ko.append(station_id)

print("\n--- RESUME ---")
print(f"Stations OK : {stations_ok}")
print(f"Stations KO : {stations_ko}")
print("--- FIN ---")