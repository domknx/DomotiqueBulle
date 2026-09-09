# dashboard-api

Première tranche réelle du service applicatif prévu au §4 du cahier des charges
(`dashboard/CAHIER_DES_CHARGES.md`) — voir aussi §7 (modèle de configuration) et
`custom_dashboard.md` (mémoire projet) pour l'historique de la décision.

**Ce qui existe aujourd'hui (09.09.2026)** : un seul endpoint, `GET /api/weather`, qui
interroge Open-Meteo (coordonnées + nombre de jours dans `dashboard/config/weather.yaml`) et
rend une liste de jours dans le vocabulaire déjà utilisé par le frontend (`sunny`, `cloudy`,
`rainy`, `stormy`, `snowy`, `clear-night`). Pas de connexion à Home Assistant à ce stade — la
météo n'en a pas besoin.

**Ce qui n'existe pas encore** : la connexion WebSocket à Home Assistant, le modèle de domaine
Pydantic pour les autres sections (pièces, énergie, scènes...), le moteur de suggestions (T6).
À construire par incréments successifs.

## Lancer en local (hors Docker)

```
cd dashboard/api
pip install -r requirements.txt
mkdir -p /tmp/dashboard-config && cp ../config/weather.yaml /tmp/dashboard-config/
CONFIG_DIR=/tmp/dashboard-config uvicorn app.main:app --reload
```

(En Docker, `dashboard/config/` est monté directement sur `/config` — voir `docker-compose.yml`.)
