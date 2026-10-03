#!/bin/bash
# Fonctions communes aux scripts de mise à jour de Home Assistant (03.10.2026) :
# ha_update.sh, ha_restore.sh, ha_update_agent.sh. Fichier à "sourcer", pas à exécuter.
#
# Écrit pour le bash 3.2 livré avec macOS et les outils BSD du Mac mini (pas de GNU sed/date,
# pas de Python ni de jq) : d'où les fichiers d'état en « clé=valeur », relus par dashboard-api.

# launchd démarre les scripts avec un PATH minimal : on ajoute les emplacements possibles de
# la commande docker installée par Docker Desktop.
PATH="/usr/local/bin:/opt/homebrew/bin:/Applications/Docker.app/Contents/Resources/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
export PATH

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

HA_SERVICE="homeassistant"
HA_CONTAINER="homeassistant"
HA_IMAGE_REPO="homeassistant/home-assistant"
HA_DATA_NAME="HomeAssistant_Data"
HA_DATA_DIR="${PROJECT_ROOT}/${HA_DATA_NAME}"
HA_URL="http://localhost:8123/manifest.json"
ENV_FILE="${PROJECT_ROOT}/.env"

STATE_DIR="${PROJECT_ROOT}/dashboard/version/state"
REQ_DIR="${STATE_DIR}/requests"
STATUS_FILE="${STATE_DIR}/update_status"
HEARTBEAT_FILE="${STATE_DIR}/agent_heartbeat"
LOCK_DIR="${STATE_DIR}/update.lock"
LOG_FILE="${STATE_DIR}/update.log"

BACKUP_ROOT="${PROJECT_ROOT}/Backups/ha_update"
NAS_ROOT="/Volumes/Sauvegardes/0_Domotique"
NAS_DIR="${NAS_ROOT}/ha_update"
LOCAL_RETENTION=5

# Délais de vérification après démarrage (secondes) ; surchargeables pour les essais.
HA_VERIFY_TIMEOUT="${HA_VERIFY_TIMEOUT:-900}"
HA_ROLLBACK_TIMEOUT="${HA_ROLLBACK_TIMEOUT:-600}"
HA_STABILITY_WAIT="${HA_STABILITY_WAIT:-60}"

VERSION_RE='^20[0-9][0-9]\.[0-9]{1,2}\.[0-9]{1,2}$'

# Renseignées par le script appelant, reprises dans chaque écriture d'état.
ST_FROM=""
ST_TO=""
ST_BACKUP=""
ST_STARTED=""

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*"; }

now_utc() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }

valid_version() { [[ "${1:-}" =~ $VERSION_RE ]]; }

# version_gt A B : vrai si A est strictement plus récente que B.
version_gt() {
  [ "$1" != "$2" ] || return 1
  [ "$(printf '%s\n%s\n' "$1" "$2" | sort -t. -k1,1n -k2,2n -k3,3n | tail -n 1)" = "$1" ]
}

dc() { (cd "$PROJECT_ROOT" && docker compose "$@"); }

touch_heartbeat() {
  mkdir -p "$STATE_DIR" 2>/dev/null
  now_utc > "$HEARTBEAT_FILE" 2>/dev/null
}

# write_status ETAT ETAPE MESSAGE — écriture atomique (fichier temporaire puis renommage).
write_status() {
  local state="$1" step="$2" message="$3" finished=""
  [ "$state" = "running" ] || finished="$(now_utc)"
  mkdir -p "$STATE_DIR"
  {
    echo "state=${state}"
    echo "step=${step}"
    echo "message=$(printf '%s' "$message" | tr '\n\r' '  ')"
    echo "from=${ST_FROM}"
    echo "to=${ST_TO}"
    echo "backup=${ST_BACKUP}"
    echo "started_at=${ST_STARTED}"
    echo "finished_at=${finished}"
  } > "${STATUS_FILE}.tmp" && mv -f "${STATUS_FILE}.tmp" "$STATUS_FILE"
  log "[${state}/${step}] ${message}"
}

installed_version() { tr -d '[:space:]' < "${HA_DATA_DIR}/.HA_VERSION" 2>/dev/null; }

ha_running() { [ "$(docker inspect -f '{{.State.Running}}' "$HA_CONTAINER" 2>/dev/null)" = "true" ]; }

ha_http_ok() { curl -fsS -o /dev/null -m 5 "$HA_URL" 2>/dev/null; }

# wait_for_ha VERSION DELAI_S : attend que le conteneur tourne, que l'interface réponde et que HA
# annonce bien VERSION, puis revérifie HA_STABILITY_WAIT secondes plus tard (pour ne pas valider un démarrage
# qui retombe aussitôt, comme une boucle de redémarrage).
wait_for_ha() {
  local expected="$1" timeout_s="$2" waited=0
  while [ "$waited" -lt "$timeout_s" ]; do
    touch_heartbeat
    if ha_running && ha_http_ok && [ "$(installed_version)" = "$expected" ]; then
      log "Home Assistant ${expected} répond ; contrôle de stabilité dans ${HA_STABILITY_WAIT} s."
      sleep "$HA_STABILITY_WAIT"
      touch_heartbeat
      if ha_running && ha_http_ok && [ "$(installed_version)" = "$expected" ]; then
        return 0
      fi
      log "Home Assistant ne répond plus après ${HA_STABILITY_WAIT} s ; on continue d'attendre."
      waited=$((waited + HA_STABILITY_WAIT))
    fi
    sleep 10
    waited=$((waited + 10))
  done
  return 1
}

# set_image_tag VERSION : fixe la version de l'image dans .env (HA_IMAGE_TAG), lue par
# docker-compose.yml. Le contenu de .env est réécrit sur place pour garder ses droits d'accès.
set_image_tag() {
  local version="$1" tmp
  [ -f "$ENV_FILE" ] || { log "Fichier .env introuvable."; return 1; }
  tmp="$(mktemp "${TMPDIR:-/tmp}/ha_env.XXXXXX")" || return 1
  grep -v '^HA_IMAGE_TAG=' "$ENV_FILE" > "$tmp"
  if [ -s "$tmp" ] && [ -n "$(tail -c 1 "$tmp")" ]; then echo >> "$tmp"; fi
  echo "HA_IMAGE_TAG=${version}" >> "$tmp"
  cat "$tmp" > "$ENV_FILE"
  local rc=$?
  rm -f "$tmp"
  return $rc
}

# Verrou : un seul script de mise à jour ou de restauration à la fois. Un verrou laissé par un
# script interrompu (Mac redémarré en cours de route) est reconnu grâce au numéro de processus.
lock_is_stale() {
  local pid
  [ -d "$LOCK_DIR" ] || return 1
  pid="$(cat "${LOCK_DIR}/pid" 2>/dev/null)"
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null && return 1
  return 0
}

acquire_lock() {
  mkdir -p "$STATE_DIR"
  if lock_is_stale; then rm -rf "$LOCK_DIR"; fi
  mkdir "$LOCK_DIR" 2>/dev/null || return 1
  echo "$$" > "${LOCK_DIR}/pid"
  return 0
}

release_lock() { rm -rf "$LOCK_DIR" 2>/dev/null; }

# Recopie d'une sauvegarde sur le disque externe, si celui-ci est branché. Jamais bloquant.
copy_backup_to_nas() {
  local bk="$1" name
  name="$(basename "$bk")"
  if [ ! -d "$NAS_ROOT" ]; then
    log "Disque externe non monté (${NAS_ROOT}) : la sauvegarde reste en local uniquement."
    return 1
  fi
  mkdir -p "${NAS_DIR}/${name}" || { log "Impossible d'écrire sur le disque externe."; return 1; }
  cp "${bk}/${HA_DATA_NAME}.tar.gz" "${bk}/info.txt" "${bk}/env.backup" "${NAS_DIR}/${name}/" 2>/dev/null \
    || { log "Copie sur le disque externe incomplète."; return 1; }
  log "Sauvegarde copiée sur le disque externe : ${NAS_DIR}/${name}"
  return 0
}

# Rétention locale : on garde les LOCAL_RETENTION sauvegardes les plus récentes ; une plus
# ancienne n'est supprimée que si sa copie existe sur le disque externe (même règle que
# backup_jalon.sh).
apply_retention() {
  local old
  [ -d "$BACKUP_ROOT" ] || return 0
  [ -d "$NAS_DIR" ] || { log "Rétention ignorée : disque externe non monté."; return 0; }
  (cd "$BACKUP_ROOT" && ls -1dt */ 2>/dev/null | tail -n +$((LOCAL_RETENTION + 1))) | while read -r old; do
    old="${old%/}"
    if [[ "$old" =~ ^[0-9]{8}_[0-9]{6}_ ]] && [ -f "${NAS_DIR}/${old}/${HA_DATA_NAME}.tar.gz" ]; then
      log "Suppression de l'ancienne sauvegarde locale (présente sur le disque externe) : ${old}"
      rm -rf "${BACKUP_ROOT:?}/${old}"
    fi
  done
}
