"""Page « Version » du dashboard — suivi des versions de Home Assistant (03.10.2026).

Ce module répond à quatre questions, et rien d'autre :

1. quelle version de Home Assistant tourne ici ? (fichier `.HA_VERSION` de HA, monté seul et en
   lecture seule — dashboard-api n'a accès à rien d'autre dans HomeAssistant_Data) ;
2. quelle est la dernière version publiée ? (version.home-assistant.io, la source officielle ;
   résultat mis en cache dans /data/state/latest.json) ;
3. que dit la dernière analyse de Claude ? (/data/ha_release_analysis.json, réécrit chaque
   vendredi soir par une tâche planifiée — voir dashboard/version/README.md) ;
4. où en est une mise à jour demandée depuis la page ?

Le bouton de mise à jour est protégé par un mot de passe, vérifié ICI (côté serveur) et jamais
dans la page : seule son empreinte salée (PBKDF2-SHA256) est conservée, dans
/data/update_password.hash, hors Git. Cinq erreurs de suite bloquent le bouton dix minutes.
Pour le changer : docker exec -it dashboard-api python -m app.set_password

IMPORTANT — ce service ne touche jamais à Docker. Le bouton « Sauvegarder et mettre à jour » se
contente de déposer un fichier de demande dans /data/state/requests/ ; c'est un agent launchd côté
Mac (scripts/ha_update_agent.sh) qui le ramasse et lance scripts/ha_update.sh. Aucun accès au
socket Docker n'est donc donné à un conteneur joignable depuis le web. Les fichiers échangés avec
cet agent sont du texte « clé=valeur » (une ligne par clé), pour rester lisibles par bash sans
dépendre de Python ou de jq sur le Mac.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

DATA_DIR = Path(os.environ.get("VERSION_DATA_DIR", "/data"))
STATE_DIR = DATA_DIR / "state"
REQUESTS_DIR = STATE_DIR / "requests"
ANALYSIS_PATH = DATA_DIR / "ha_release_analysis.json"
LATEST_CACHE_PATH = STATE_DIR / "latest.json"
STATUS_PATH = STATE_DIR / "update_status"
HEARTBEAT_PATH = STATE_DIR / "agent_heartbeat"
REQUEST_PATH = REQUESTS_DIR / "update_request"
PASSWORD_PATH = DATA_DIR / "update_password.hash"
AUTH_STATE_PATH = STATE_DIR / "auth_failures.json"
HA_VERSION_FILE = Path(os.environ.get("HA_VERSION_FILE", "/ha/HA_VERSION"))

# Sources officielles ; surchargeables par variable d'environnement pour les tests hors ligne.
STABLE_URL = os.environ.get("HA_STABLE_URL", "https://version.home-assistant.io/stable.json")
GITHUB_RELEASE_URL = os.environ.get(
    "HA_RELEASE_URL", "https://api.github.com/repos/home-assistant/core/releases/tags/{version}"
)

# Une version stable de HA : AAAA.M.P (ex. 2026.9.4). Sert aussi de garde-fou de sécurité : la
# valeur finit dans une ligne de commande côté Mac, rien d'autre que ce format ne passe.
VERSION_RE = re.compile(r"^20\d{2}\.\d{1,2}\.\d{1,2}$")

# Filet de sécurité : si personne (ni la tâche du vendredi, ni le bouton) n'a vérifié depuis ce
# délai, la lecture de la page relance une vérification toute seule.
AUTO_REFRESH_AFTER_S = 8 * 24 * 3600
# L'agent du Mac écrit son témoin toutes les minutes ; au-delà de ce délai on le considère absent.
AGENT_ALIVE_WITHIN_S = 5 * 60
# Une demande que l'agent n'a pas prise en charge dans ce délai est considérée comme perdue.
REQUEST_STALE_AFTER_S = 10 * 60

LEVELS = ("green", "yellow", "red")

# Mot de passe du bouton de mise à jour.
PBKDF2_ITERATIONS = 200_000
MAX_PASSWORD_FAILURES = 5
PASSWORD_LOCK_S = 10 * 60


class VersionError(Exception):
    """Erreur métier renvoyée telle quelle à la page (message en français)."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_version(value: str) -> tuple[int, int, int] | None:
    if not isinstance(value, str) or not VERSION_RE.match(value.strip()):
        return None
    year, month, patch = value.strip().split(".")
    return int(year), int(month), int(patch)


def is_newer(candidate: str | None, reference: str | None) -> bool:
    a, b = parse_version(candidate or ""), parse_version(reference or "")
    return bool(a and b and a > b)


def read_installed() -> str | None:
    try:
        value = HA_VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value if parse_version(value) else None


def _read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _read_keyvalue(path: Path) -> dict[str, str]:
    """Lit un fichier « clé=valeur » écrit par les scripts bash du Mac."""
    out: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                out[key.strip()] = val.strip()
    except OSError:
        pass
    return out


def hash_password(password: str, salt: bytes | None = None, iterations: int = PBKDF2_ITERATIONS) -> str:
    """Empreinte au format « pbkdf2_sha256:itérations:sel:empreinte » (hexadécimal)."""
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256:{iterations}:{salt.hex()}:{digest.hex()}"


def password_is_set() -> bool:
    return _password_record() is not None


def _password_record() -> tuple[int, bytes, bytes] | None:
    try:
        algo, iterations, salt, digest = PASSWORD_PATH.read_text(encoding="utf-8").strip().split(":")
        if algo != "pbkdf2_sha256":
            return None
        return int(iterations), bytes.fromhex(salt), bytes.fromhex(digest)
    except (OSError, ValueError):
        return None


def check_password(password: str) -> None:
    """Lève VersionError si le mot de passe est absent, faux, ou si le bouton est bloqué."""
    record = _password_record()
    if record is None:
        raise VersionError(
            "Aucun mot de passe de mise à jour n'est configuré : mise à jour refusée "
            "(docker exec -it dashboard-api python -m app.set_password).",
            503,
        )

    now = time.time()
    state = _read_json(AUTH_STATE_PATH)
    state = state if isinstance(state, dict) else {}
    locked_until = float(state.get("locked_until") or 0)
    if now < locked_until:
        minutes = max(1, int((locked_until - now + 59) // 60))
        raise VersionError(f"Trop d'essais. Nouvel essai possible dans {minutes} min.", 429)

    iterations, salt, expected = record
    digest = hashlib.pbkdf2_hmac("sha256", (password or "").encode("utf-8"), salt, iterations)
    if hmac.compare_digest(digest, expected):
        if state:
            _write_atomic(AUTH_STATE_PATH, json.dumps({"failures": 0, "locked_until": 0}))
        return

    failures = int(state.get("failures") or 0) + 1
    if failures >= MAX_PASSWORD_FAILURES:
        _write_atomic(AUTH_STATE_PATH, json.dumps({"failures": 0, "locked_until": now + PASSWORD_LOCK_S}))
        raise VersionError("Mot de passe incorrect. Trop d'essais : bouton bloqué pendant 10 minutes.", 429)
    _write_atomic(AUTH_STATE_PATH, json.dumps({"failures": failures, "locked_until": 0}))
    left = MAX_PASSWORD_FAILURES - failures
    raise VersionError(f"Mot de passe incorrect ({left} essai{'s' if left > 1 else ''} restant{'s' if left > 1 else ''}).", 401)


async def fetch_latest(source: str) -> dict[str, Any]:
    """Interroge la source officielle et met le résultat en cache. Lève VersionError si échec."""
    # Deux appels au plus, 6 s chacun : on reste sous le délai du proxy nginx (15 s).
    try:
        async with httpx.AsyncClient(timeout=6.0, headers={"User-Agent": "villa-bulle-dashboard"}) as client:
            resp = await client.get(STABLE_URL)
            resp.raise_for_status()
            version = str(resp.json()["homeassistant"]["default"]).strip()
            if not parse_version(version):
                raise ValueError(f"version inattendue : {version!r}")

            # Date de publication : confort d'affichage uniquement (API GitHub sans jeton, limitée
            # à 60 requêtes/heure) — une erreur ici ne fait pas échouer la vérification.
            released_at = None
            try:
                rel = await client.get(GITHUB_RELEASE_URL.format(version=version))
                if rel.status_code == 200:
                    released_at = (rel.json().get("published_at") or "")[:10] or None
            except (httpx.HTTPError, ValueError):
                released_at = None
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise VersionError(f"Impossible de joindre version.home-assistant.io : {exc}", 502) from exc

    previous = _read_json(LATEST_CACHE_PATH) or {}
    if released_at is None and previous.get("version") == version:
        released_at = previous.get("released_at")

    latest = {"version": version, "released_at": released_at, "checked_at": _now_iso(), "source": source}
    _write_atomic(LATEST_CACHE_PATH, json.dumps(latest, ensure_ascii=False, indent=2))
    return latest


def _cache_age_s(latest: dict[str, Any] | None) -> float | None:
    if not latest or not latest.get("checked_at"):
        return None
    try:
        checked = datetime.fromisoformat(latest["checked_at"])
    except ValueError:
        return None
    if checked.tzinfo is None:
        checked = checked.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - checked).total_seconds()


def load_analysis() -> dict[str, Any] | None:
    data = _read_json(ANALYSIS_PATH)
    if not isinstance(data, dict) or not parse_version(str(data.get("version", ""))):
        return None
    reco = data.get("recommendation")
    if not isinstance(reco, dict) or reco.get("level") not in LEVELS:
        return None
    return data


def build_recommendation(installed: str | None, latest_version: str | None, analysis: dict[str, Any] | None) -> dict[str, Any]:
    """Recommandation affichée sur le bouton. Prudente par défaut : sans analyse, c'est rouge."""
    if not installed or not latest_version:
        missing = "installée" if not installed else "publiée"
        return {"level": "unknown", "label": "Version inconnue", "reason": f"La version {missing} n'a pas pu être lue."}
    if not is_newer(latest_version, installed):
        return {"level": "none", "label": "Home Assistant est à jour", "reason": ""}
    if analysis is None:
        return {
            "level": "red",
            "label": "Pas encore analysée",
            "reason": "Aucune analyse disponible pour cette version. La prochaine vérification du vendredi soir la produira.",
        }
    if analysis["version"] != latest_version:
        return {
            "level": "red",
            "label": "Pas encore analysée",
            "reason": (
                f"La dernière analyse porte sur la version {analysis['version']}, pas sur la {latest_version} "
                "publiée depuis. Elle sera refaite lors de la vérification du vendredi soir."
            ),
        }
    reco = analysis["recommendation"]
    return {
        "level": reco["level"],
        "label": str(reco.get("label", "")),
        "reason": str(reco.get("reason", "")),
    }


def agent_state() -> dict[str, Any]:
    try:
        age = time.time() - HEARTBEAT_PATH.stat().st_mtime
    except OSError:
        return {"alive": False, "last_seen_s": None}
    return {"alive": age <= AGENT_ALIVE_WITHIN_S, "last_seen_s": int(age)}


def _pct(value: str | None) -> int | None:
    """Pourcentage écrit par le script (0 à 100), ou None s'il n'a pas commencé."""
    try:
        return max(0, min(100, int(value)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def update_state() -> dict[str, Any]:
    """État de la mise à jour, vu depuis les fichiers échangés avec l'agent du Mac."""
    status = _read_keyvalue(STATUS_PATH)
    state = status.get("state", "idle")
    out: dict[str, Any] = {
        "state": state if state in ("idle", "running", "success", "failed", "rolled_back") else "idle",
        "step": status.get("step", ""),
        "message": status.get("message", ""),
        "from": status.get("from", ""),
        "to": status.get("to", ""),
        "backup": status.get("backup", ""),
        "backup_pct": _pct(status.get("backup_pct")),
        "update_pct": _pct(status.get("update_pct")),
        "started_at": status.get("started_at", ""),
        "finished_at": status.get("finished_at", ""),
    }
    if REQUEST_PATH.exists():
        req = _read_keyvalue(REQUEST_PATH)
        try:
            age = time.time() - REQUEST_PATH.stat().st_mtime
        except OSError:
            age = 0
        if out["state"] != "running":
            out.update(
                {
                    "state": "requested",
                    "step": "",
                    "to": req.get("version", ""),
                    "message": (
                        "Demande en attente depuis plus de 10 minutes : l'agent du Mac ne l'a pas prise en charge."
                        if age > REQUEST_STALE_AFTER_S
                        else "Demande transmise, en attente de l'agent du Mac."
                    ),
                    "stale": age > REQUEST_STALE_AFTER_S,
                }
            )
    return out


async def get_status(force_check: bool = False, source: str = "manual") -> dict[str, Any]:
    installed = read_installed()
    latest = _read_json(LATEST_CACHE_PATH)
    check_error = None

    age = _cache_age_s(latest)
    needs_refresh = force_check or latest is None or age is None or age > AUTO_REFRESH_AFTER_S
    if needs_refresh:
        try:
            latest = await fetch_latest(source if force_check else "auto")
        except VersionError as exc:
            if force_check:
                raise
            check_error = exc.message  # lecture simple de la page : on garde le cache, on signale

    latest_version = (latest or {}).get("version")
    analysis = load_analysis()
    return {
        "installed": installed,
        "latest": latest,
        "check_error": check_error,
        "update_available": is_newer(latest_version, installed),
        "analysis": analysis,
        "analysis_current": bool(analysis and analysis["version"] == latest_version),
        "recommendation": build_recommendation(installed, latest_version, analysis),
        "agent": agent_state(),
        "password_set": password_is_set(),
        "update": update_state(),
    }


async def request_update(version: str, password: str) -> dict[str, Any]:
    """Dépose la demande de mise à jour pour l'agent du Mac, après toutes les vérifications.

    Le mot de passe est contrôlé en dernier : une demande refusée pour une autre raison (version
    périmée, mise à jour déjà en cours, agent absent) ne consomme pas d'essai.
    """
    version = (version or "").strip()
    if not parse_version(version):
        raise VersionError("Numéro de version invalide.")

    installed = read_installed()
    latest = _read_json(LATEST_CACHE_PATH) or {}
    if not installed:
        raise VersionError("Version installée inconnue : mise à jour refusée par prudence.", 409)
    if version != latest.get("version"):
        raise VersionError("Cette version n'est pas la dernière version connue. Relance une vérification.", 409)
    if not is_newer(version, installed):
        raise VersionError("Cette version n'est pas plus récente que la version installée.", 409)

    current = update_state()
    if current["state"] in ("running", "requested") and not current.get("stale"):
        raise VersionError("Une mise à jour est déjà en cours ou en attente.", 409)
    if not agent_state()["alive"]:
        raise VersionError(
            "L'agent de mise à jour ne répond pas sur le Mac mini (voir scripts/install_ha_update_agent.sh).", 503
        )

    check_password(password)

    reco = build_recommendation(installed, version, load_analysis())
    _write_atomic(
        REQUEST_PATH,
        f"version={version}\nfrom={installed}\nrequested_at={_now_iso()}\nrecommendation={reco['level']}\n",
    )
    return {"accepted": True, "version": version, "from": installed}
