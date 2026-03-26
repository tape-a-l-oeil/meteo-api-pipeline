import os
import time
import requests
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("METEOFRANCE_API_KEY")
if not API_KEY:
    raise RuntimeError("Cle API absente")

URL_STATIONS = "https://public-api.meteofrance.fr/public/DPClim/v1/liste-stations/quotidienne"
URL_COMMANDE = "https://public-api.meteofrance.fr/public/DPClim/v1/commande-station/quotidienne"
URL_DOWNLOAD = "https://public-api.meteofrance.fr/public/DPClim/v1/commande/fichier"

# France metropolitaine uniquement ici
departements = [f"{i:02d}" for i in range(1, 96)] + ["2A", "2B"]

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

wait_between_departements = 1
wait_between_stations = 1
wait_before_download = 2
wait_retry = 2

stations_ok = []
stations_ko = []
departements_ko = []


def extraire_stations(payload):
    """
    Essaie de recuperer une liste de stations quel que soit le format exact renvoye.
    """
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in [
            "listeStations",
            "stations",
            "response",
            "results",
            "features"
        ]:
            value = payload.get(key)
            if isinstance(value, list):
                return value

    return []


def extraire_id_station(station):
    """
    Essaie de recuperer l identifiant station selon plusieurs noms possibles.
    """
    for key in ["id", "id_station", "idStation", "NUM_POSTE", "num_poste"]:
        value = station.get(key)
        if value:
            return str(value)
    return None


def extraire_id_commande(payload):
    if "elaboreProduitAvecDemandeResponse" in payload:
        return payload["elaboreProduitAvecDemandeResponse"].get("return")

    for key in ["idCommande", "id_commande", "idCmde"]:
        value = payload.get(key)
        if value:
            return value

    return None


def recuperer_stations_departement(code_departement):
    params = {"id-departement": code_departement}

    try:
        r = requests.get(URL_STATIONS, headers=headers_json, params=params, timeout=30)
    except requests.RequestException as e:
        print(f"Erreur reseau liste stations departement {code_departement} - {e}")
        return []

    if r.status_code != 200:
        print(f"Erreur liste stations departement {code_departement} - {r.status_code} - {r.text}")
        return []

    try:
        payload = r.json()
    except ValueError:
        print(f"Reponse JSON invalide departement {code_departement}")
        return []

    stations = extraire_stations(payload)

    ids = []
    for station in stations:
        if isinstance(station, dict):
            station_id = extraire_id_station(station)
            if station_id:
                ids.append(station_id)

    return list(dict.fromkeys(ids))  # dedup propre


for departement in departements:
    print(f"\n===== DEPARTEMENT {departement} =====")
    time.sleep(wait_between_departements)

    station_ids = recuperer_stations_departement(departement)

    if not station_ids:
        print(f"Aucune station trouvee pour {departement}")
        departements_ko.append(departement)
        continue

    print(f"{len(station_ids)} station(s) trouvee(s)")

    for station_id in station_ids:
        print(f"\n--- Station {station_id} ---")
        time.sleep(wait_between_stations)

        id_commande = None

        # 1. Creation commande
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
                time.sleep(wait_retry)
                continue

            if r.status_code == 202:
                try:
                    payload = r.json()
                except ValueError:
                    print("Erreur JSON commande")
                    time.sleep(wait_retry)
                    continue

                id_commande = extraire_id_commande(payload)

                if id_commande:
                    print(f"id_commande = {id_commande}")
                    break
                else:
                    print(f"id_commande introuvable - payload : {payload}")
                    time.sleep(wait_retry)

            elif r.status_code == 500:
                print("API instable sur commande")
                time.sleep(wait_retry)

            else:
                print(f"Erreur commande - {r.status_code} - {r.text}")
                time.sleep(wait_retry)

        if not id_commande:
            print(f"Echec commande station {station_id}")
            stations_ko.append(station_id)
            continue

        # 2. Attente avant download
        time.sleep(wait_before_download)

        # 3. Download
        downloaded = False

        for attempt in range(1, 6):
            print(f"Download tentative {attempt}/5")

            params_dl = {"id-cmde": id_commande}

            try:
                r_dl = requests.get(URL_DOWNLOAD, headers=headers_csv, params=params_dl, timeout=60)
            except requests.RequestException as e:
                print(f"Erreur reseau download - {e}")
                time.sleep(wait_retry)
                continue

            if r_dl.status_code == 201:
                filepath = f"csv/meteo_{station_id}_{target_date}.csv"
                with open(filepath, "wb") as f:
                    f.write(r_dl.content)

                print(f"CSV OK : {filepath}")
                stations_ok.append(station_id)
                downloaded = True
                break

            elif r_dl.status_code == 204:
                print("Fichier en cours de generation")
                time.sleep(wait_retry)

            elif r_dl.status_code == 404:
                print("Pas de donnees pour cette periode")
                break

            elif r_dl.status_code == 500:
                print("API instable sur download")
                time.sleep(wait_retry)

            else:
                print(f"Erreur download - {r_dl.status_code} - {r_dl.text}")
                break

        if not downloaded:
            stations_ko.append(station_id)

print("\n===== RESUME =====")
print(f"Stations OK : {len(stations_ok)}")
print(f"Stations KO : {len(stations_ko)}")
print(f"Departements KO : {departements_ko}")
print("===== FIN =====")