"""Client Open-Meteo et traduction vers le modèle de domaine du dashboard.

Ce module ne connaît rien de Home Assistant ni du reste de dashboard-api : il prend des
coordonnées + un nombre de jours, et rend une liste de jours dans le vocabulaire déjà utilisé
par le frontend (dashboard_web_nginx/index.html, avant ce service : générateur mock FORECAST).
Garder ce vocabulaire strictement identique (mêmes clés, mêmes valeurs possibles pour `cond`)
est ce qui permet de brancher ce service sans réécrire l'affichage.
"""

from __future__ import annotations

from typing import Any

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Table des codes météo WMO (norme WMO 4677, stable — utilisée telle quelle par Open-Meteo,
# voir https://open-meteo.com/en/docs) vers les 6 conditions connues du frontend. Un code
# inconnu (WMO en ajoute rarement) retombe sur "cloudy" plutôt que de faire échouer la requête.
_CLEAR = {0, 1}  # ciel clair / dégagé
_CLOUDY = {2, 3, 45, 48}  # partiellement nuageux, couvert, brouillard (pas d'icône brouillard dédiée)
_RAINY = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}  # bruine, pluie, averses
_SNOWY = {71, 73, 75, 77, 85, 86}  # neige, averses de neige
_STORMY = {95, 96, 99}  # orage, avec ou sans grêle


def condition_for(weather_code: int, is_day: bool) -> str:
    code = int(weather_code)
    if code in _STORMY:
        return "stormy"
    if code in _SNOWY:
        return "snowy"
    if code in _RAINY:
        return "rainy"
    if code in _CLOUDY:
        return "cloudy"
    if code in _CLEAR:
        return "sunny" if is_day else "clear-night"
    return "cloudy"


async def fetch_forecast(latitude: float, longitude: float, days: int, timezone: str) -> dict[str, Any]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "forecast_days": days,
        "current": "temperature_2m,relative_humidity_2m,weather_code,is_day,wind_speed_10m,pressure_msl",
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max,relative_humidity_2m_mean,"
            "wind_speed_10m_max,pressure_msl_mean"
        ),
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(OPEN_METEO_URL, params=params)
        resp.raise_for_status()
        return resp.json()


def to_dashboard_days(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Traduit une réponse brute Open-Meteo en liste de jours au format du frontend.

    Chaque jour : {date, cond, hi, lo, precip, humidity, wind, pressure} — exactement les
    champs que produisait genForecast() côté mock, plus `wind`/`pressure` en valeurs réelles
    (le mock les inventait à partir de la condition, faute de vraie source). Le jour 0 reçoit en
    plus `now` (température instantanée réelle) et sa condition est recalculée à partir du bloc
    `current` d'Open-Meteo plutôt que de l'agrégat journalier, pour savoir s'il fait nuit
    maintenant (seul le jour 0 peut être "clear-night", comme dans le mock).
    """
    daily = raw["daily"]
    current = raw.get("current")
    out: list[dict[str, Any]] = []
    for i in range(len(daily["time"])):
        out.append(
            {
                "date": daily["time"][i],
                "cond": condition_for(daily["weather_code"][i], is_day=True),
                "hi": round(daily["temperature_2m_max"][i]),
                "lo": round(daily["temperature_2m_min"][i]),
                "precip": round(daily["precipitation_probability_max"][i] or 0),
                "humidity": round(daily["relative_humidity_2m_mean"][i]),
                "wind": round(daily["wind_speed_10m_max"][i]),
                "pressure": round(daily["pressure_msl_mean"][i]),
            }
        )

    if out and current:
        out[0]["cond"] = condition_for(current["weather_code"], is_day=bool(current["is_day"]))
        out[0]["now"] = round(current["temperature_2m"])

    return out
