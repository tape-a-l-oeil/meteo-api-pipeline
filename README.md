# Meteo Data Pipeline

Pipeline de récupération et d’enrichissement des données météo via l’API Météo-France.

## Fonctionnalités

- Récupération des stations météo (France entière)
- Téléchargement des données quotidiennes (CSV)
- Gestion des erreurs et retries API
- Enrichissement géographique :
  - commune (API Geo)
  - code postal
  - reverse geocoding (lat/lon)

## Stack

- Python (requests, pandas)
- API Météo-France
- API Geo (geo.api.gouv.fr)
- OpenStreetMap (Nominatim)

## Structure

```text
API Météo-France
→ récupération stations
→ téléchargement CSV
→ enrichissement
→ préparation Snowflake
