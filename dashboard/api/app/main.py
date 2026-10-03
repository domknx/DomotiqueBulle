"""dashboard-api — première tranche réelle (météo uniquement, 09.09.2026).

Ce service est la toute première brique de la couche `dashboard-api` prévue au §4 du cahier des
charges (dashboard/CAHIER_DES_CHARGES.md). Volontairement réduit à un seul domaine pour l'instant :
proxy Open-Meteo pour l'écran Météo (A2, M1-M6). Pas encore de connexion WebSocket à Home
Assistant ni de modèle de domaine pour les autres sections (pièces, énergie, scènes...) —
viendra par incréments successifs, voir §12 (points ouverts) du cahier des charges.

03.10.2026 : deuxième tranche, page « Version » (suivi des versions de Home Assistant, analyse
hebdomadaire, demande de mise à jour) — voir ha_version.py et dashboard/version/README.md.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import ha_version, weather

# /config est le point de montage utilisé en Docker (dashboard/config/ monté en lecture seule,
# voir docker-compose.yml) ; CONFIG_DIR reste modifiable par variable d'env pour lancer le
# service hors Docker (voir README.md de ce dossier).
CONFIG_PATH = Path(os.environ.get("CONFIG_DIR", "/config")) / "weather.yaml"

app = FastAPI(title="dashboard-api", description="Villa Bulle — service dashboard (météo, versions)")


def load_weather_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"Config manquante : {CONFIG_PATH} (montage Docker absent ?)")
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/weather")
async def get_weather() -> dict[str, Any]:
    cfg = load_weather_config()
    days = max(int(cfg.get("days_home", 5)), int(cfg.get("days_detail", 15)))

    try:
        raw = await weather.fetch_forecast(
            latitude=cfg["latitude"],
            longitude=cfg["longitude"],
            days=days,
            timezone=cfg.get("timezone", "Europe/Zurich"),
        )
    except Exception as exc:  # httpx.HTTPError et variantes — Open-Meteo injoignable/en erreur
        raise HTTPException(status_code=502, detail=f"Open-Meteo injoignable : {exc}") from exc

    return {
        "source": cfg.get("provider", "open-meteo"),
        "location": {"latitude": cfg["latitude"], "longitude": cfg["longitude"]},
        "days": weather.to_dashboard_days(raw),
    }


# ---------------------------------------------------------------------------------------------
# Page « Version » (03.10.2026) — voir ha_version.py pour le détail et les garde-fous.
# ---------------------------------------------------------------------------------------------


class UpdateRequest(BaseModel):
    version: str
    confirm: bool = False


def _version_http_error(exc: ha_version.VersionError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)


@app.get("/api/ha-version")
async def get_ha_version() -> dict[str, Any]:
    """Lecture simple (cache) : version installée, dernière version connue, analyse, état."""
    return await ha_version.get_status(force_check=False)


@app.post("/api/ha-version/check")
async def check_ha_version() -> dict[str, Any]:
    """Bouton « Vérifier maintenant » : interroge réellement la source officielle."""
    try:
        return await ha_version.get_status(force_check=True, source="manual")
    except ha_version.VersionError as exc:
        raise _version_http_error(exc) from exc


@app.post("/api/ha-version/update")
async def update_ha_version(req: UpdateRequest) -> dict[str, Any]:
    """Bouton « Sauvegarder et mettre à jour » : dépose une demande pour l'agent du Mac."""
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Confirmation manquante.")
    try:
        return await ha_version.request_update(req.version)
    except ha_version.VersionError as exc:
        raise _version_http_error(exc) from exc
