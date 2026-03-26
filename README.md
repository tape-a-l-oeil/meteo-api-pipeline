# Données Météo – Pipeline d’ingestion et enrichissement

Projet de collecte, enrichissement et préparation de données météo pour exploitation analytique.

## Objectif

Construire une chaîne de traitement permettant de :

- récupérer les données météo via l’API Météo-France
- identifier les stations météo exploitables
- enrichir les stations avec des informations géographiques et administratives
- préparer les données pour intégration dans Snowflake
- relier ensuite les données météo aux magasins

---

## Périmètre actuel

Le projet couvre actuellement plusieurs briques :

### 1. Récupération des stations météo
Appel de l’API Météo-France pour récupérer la liste des stations quotidiennes par département.

Exemple :
- récupération des stations d’un département
- lecture des métadonnées station (`id`, `nom`, `posteOuvert`, `typePoste`)

### 2. Téléchargement des données météo quotidiennes
Script Python permettant de :

- parcourir les stations météo
- lancer une commande API par station
- récupérer l’identifiant de commande
- télécharger le CSV correspondant
- gérer les délais d’attente et les retries

### 3. Enrichissement administratif via l’API Geo
Script d’enrichissement basé sur le code INSEE pour obtenir :

- la commune
- les codes postaux associés

Ce traitement permet notamment de produire un fichier enrichi à partir d’un fichier de stations en entrée.

### 4. Géocodage inverse
Script de reverse geocoding à partir des coordonnées latitude / longitude pour récupérer :

- la commune
- le code postal

Utilisé pour rattacher les stations à une localisation exploitable.

---

## Scripts présents dans le projet

### `AppelAPIcomplet.py`
Script principal de récupération des données météo :

- récupération des stations par département
- boucle sur les stations
- commande API Météo-France
- téléchargement des fichiers CSV
- gestion des erreurs et des temps d’attente

### Script de récupération de liste de stations
Permet de tester et inspecter les stations disponibles pour un département donné.

### Script d’enrichissement Geo API
Permet d’enrichir un fichier de stations avec :

- `CODE_INSEE`
- `COMMUNE`
- `CODE_POSTAL`

### Script de reverse geocoding
Permet de retrouver la commune et le code postal à partir de la latitude et de la longitude d’une station.

---

## Technologies utilisées

- Python
- Requests
- Pandas
- Dotenv
- API Météo-France
- API Geo (`geo.api.gouv.fr`)
- Nominatim / OpenStreetMap

---

## Structure logique du projet

```text
API Météo-France
→ récupération des stations
→ commande des fichiers météo
→ téléchargement CSV
→ enrichissement géographique
→ préparation pour chargement Snowflake
