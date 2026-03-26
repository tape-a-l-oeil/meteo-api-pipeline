import requests
import pandas as pd
import time

INPUT_FILE = "stations_input.csv"
OUTPUT_FILE = "stations_output.csv"

API_URL = "https://geo.api.gouv.fr/communes/{}?fields=nom,codesPostaux"


def get_commune_info(code_insee):
    try:
        response = requests.get(API_URL.format(code_insee), timeout=5)

        if response.status_code != 200:
            print(f"Erreur API pour {code_insee}")
            return None, None

        data = response.json()

        commune = data.get("nom")
        codes_postaux = data.get("codesPostaux")

        return commune, codes_postaux

    except requests.exceptions.RequestException as e:
        print(f"Exception réseau pour {code_insee}: {e}")
        return None, None


def enrich_stations():
    df = pd.read_csv(INPUT_FILE, dtype=str)

    if "NUM_POSTE" not in df.columns:
        raise ValueError("Le fichier doit contenir une colonne 'NUM_POSTE'")

    df["NUM_POSTE"] = df["NUM_POSTE"].str.strip()
    df["CODE_INSEE"] = df["NUM_POSTE"].str[:5]

    unique_insee = df["CODE_INSEE"].unique()
    cache = {}

    # Appel API avec cache pour éviter doublons
    for code_insee in unique_insee:
        commune, codes_postaux = get_commune_info(code_insee)
        cache[code_insee] = (commune, codes_postaux)
        time.sleep(0.2)  # éviter surcharge API

    # Construction du résultat explosé
    rows = []

    for _, row in df.iterrows():
        num_poste = row["NUM_POSTE"]
        code_insee = row["CODE_INSEE"]

        commune, codes_postaux = cache.get(code_insee, (None, None))

        if not codes_postaux:
            rows.append({
                "NUM_POSTE": num_poste,
                "CODE_INSEE": code_insee,
                "COMMUNE": commune,
                "CODE_POSTAL": None
            })
        else:
            # Explosion multi codes postaux (Dunkerque etc.)
            for cp in codes_postaux:
                rows.append({
                    "NUM_POSTE": num_poste,
                    "CODE_INSEE": code_insee,
                    "COMMUNE": commune,
                    "CODE_POSTAL": cp
                })

    result_df = pd.DataFrame(rows)

    result_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Fichier généré : {OUTPUT_FILE}")


if __name__ == "__main__":
    enrich_stations()
