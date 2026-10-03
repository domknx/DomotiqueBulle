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
# Progression affichée par les deux barres de la page Version (0 à 100, vide = pas commencé).
ST_BACKUP_PCT=""
ST_UPDATE_PCT=""
# Dernier état écrit, pour pouvoir réécrire le fichier quand seule la progression change.
ST_STATE="idle"
ST_STEP=""
ST_MESSAGE=""

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

# flush_status : écrit l'état courant dans le fichier lu par dashboard-api — écriture atomique
# (fichier temporaire puis renommage), sans ligne de journal.
flush_status() {
  local finished=""
  [ "$ST_STATE" = "running" ] || finished="$(now_utc)"
  mkdir -p "$STATE_DIR"
  {
    echo "state=${ST_STATE}"
    echo "step=${ST_STEP}"
    echo "message=$(printf '%s' "$ST_MESSAGE" | tr '\n\r' '  ')"
    echo "from=${ST_FROM}"
    echo "to=${ST_TO}"
    echo "backup=${ST_BACKUP}"
    echo "backup_pct=${ST_BACKUP_PCT}"
    echo "update_pct=${ST_UPDATE_PCT}"
    echo "started_at=${ST_STARTED}"
    echo "finished_at=${finished}"
  } > "${STATUS_FILE}.tmp" && mv -f "${STATUS_FILE}.tmp" "$STATUS_FILE"
}

# write_status ETAT ETAPE MESSAGE : change d'étape, écrit l'état et le consigne au journal.
write_status() {
  ST_STATE="$1"
  ST_STEP="$2"
  ST_MESSAGE="$3"
  flush_status
  log "[${ST_STATE}/${ST_STEP}] ${ST_MESSAGE}"
}

# set_progress backup|update POURCENT : fait avancer une barre. Ne recule jamais et ne réécrit
# le fichier que si la valeur change.
set_progress() {
  local which="$1" pct="$2" current
  [ "$pct" -gt 100 ] && pct=100
  if [ "$which" = "backup" ]; then current="$ST_BACKUP_PCT"; else current="$ST_UPDATE_PCT"; fi
  if [ -n "$current" ] && [ "$pct" -le "$current" ]; then return 0; fi
  if [ "$which" = "backup" ]; then ST_BACKUP_PCT="$pct"; else ST_UPDATE_PCT="$pct"; fi
  flush_status
}

installed_version() { tr -d '[:space:]' < "${HA_DATA_DIR}/.HA_VERSION" 2>/dev/null; }

ha_running() { [ "$(docker inspect -f '{{.State.Running}}' "$HA_CONTAINER" 2>/dev/null)" = "true" ]; }

ha_http_ok() { curl -fsS -o /dev/null -m 5 "$HA_URL" 2>/dev/null; }

# wait_for_ha VERSION DELAI_S [progress] : attend que le conteneur tourne, que l'interface réponde
# et que HA annonce bien VERSION, puis revérifie HA_STABILITY_WAIT secondes plus tard (pour ne pas
# valider un démarrage qui retombe aussitôt, comme une boucle de redémarrage).
# Avec « progress », fait avancer la barre « Mise à jour » sur des jalons réellement constatés :
# 15 % conteneur démarré, 35 % nouvelle version annoncée par HA, 60 % interface joignable, puis
# de 60 à 100 % le décompte du contrôle de stabilité.
wait_for_ha() {
  local expected="$1" timeout_s="$2" progress="${3:-}" waited=0 elapsed pct
  while [ "$waited" -lt "$timeout_s" ]; do
    touch_heartbeat
    if [ -n "$progress" ]; then
      pct=0
      if ha_running; then
        pct=15
        if [ "$(installed_version)" = "$expected" ]; then
          pct=35
          if ha_http_ok; then pct=60; fi
        fi
      fi
      set_progress update "$pct"
    fi
    if ha_running && ha_http_ok && [ "$(installed_version)" = "$expected" ]; then
      log "Home Assistant ${expected} répond ; contrôle de stabilité pendant ${HA_STABILITY_WAIT} s."
      elapsed=0
      while [ "$elapsed" -lt "$HA_STABILITY_WAIT" ]; do
        sleep 2
        elapsed=$((elapsed + 2))
        [ "$elapsed" -gt "$HA_STABILITY_WAIT" ] && elapsed="$HA_STABILITY_WAIT"
        [ -n "$progress" ] && set_progress update $((60 + 39 * elapsed / HA_STABILITY_WAIT))
      done
      touch_heartbeat
      if ha_running && ha_http_ok && [ "$(installed_version)" = "$expected" ]; then
        [ -n "$progress" ] && set_progress update 100
        return 0
      fi
      log "Home Assistant ne répond plus après ${HA_STABILITY_WAIT} s ; on continue d'attendre."
      waited=$((waited + HA_STABILITY_WAIT))
    fi
    sleep 5
    waited=$((waited + 5))
  done
  return 1
}

# archive_path DOSSIER : chemin de l'archive d'une sauvegarde, compressée (.tar.gz) ou non (.tar).
# L'archive est écrite non compressée pendant la mise à jour (plus rapide, et sa taille permet de
# mesurer la progression), puis compressée une fois Home Assistant reparti.
archive_path() {
  if [ -f "$1/${HA_DATA_NAME}.tar.gz" ]; then echo "$1/${HA_DATA_NAME}.tar.gz"
  elif [ -f "$1/${HA_DATA_NAME}.tar" ]; then echo "$1/${HA_DATA_NAME}.tar"
  fi
}

# backup_with_progress ARCHIVE : archive HomeAssistant_Data en faisant avancer la barre
# « Sauvegarde » d'après la taille déjà écrite, comparée à la taille du dossier. La barre reste
# à 99 % au plus tant que l'archive n'est pas terminée ET relue avec succès.
backup_with_progress() {
  local archive="$1" total_kb size_kb pid
  total_kb="$(du -sk "$HA_DATA_DIR" | awk '{print $1}')"
  [ "${total_kb:-0}" -gt 0 ] || total_kb=1
  set_progress backup 0
  tar -cf "$archive" -C "$PROJECT_ROOT" "$HA_DATA_NAME" &
  pid=$!
  while kill -0 "$pid" 2>/dev/null; do
    size_kb="$(du -k "$archive" 2>/dev/null | awk '{print $1}')"
    size_kb=$(( ${size_kb:-0} * 100 / total_kb ))
    [ "$size_kb" -gt 99 ] && size_kb=99
    set_progress backup "$size_kb"
    sleep 1
  done
  wait "$pid" || return 1
  set_progress backup 99
  tar -tf "$archive" >/dev/null || return 1
  set_progress backup 100
  return 0
}

# pull_with_progress IMAGE : télécharge l'image en indiquant le nombre de couches reçues dans le
# message d'état (lu dans la sortie de docker pull ; sans effet si le format n'est pas reconnu).
pull_with_progress() {
  local image="$1" out pid total done_n base="$ST_MESSAGE"
  out="$(mktemp "${TMPDIR:-/tmp}/ha_pull.XXXXXX")" || { docker pull "$image"; return $?; }
  docker pull "$image" > "$out" 2>&1 &
  pid=$!
  while kill -0 "$pid" 2>/dev/null; do
    touch_heartbeat
    total="$(grep -c 'Pulling fs layer' "$out")"
    done_n="$(grep -c 'Pull complete' "$out")"
    if [ "${total:-0}" -gt 0 ]; then
      ST_MESSAGE="${base} (${done_n} sur ${total} couches)"
      flush_status
    fi
    sleep 2
  done
  wait "$pid"
  local rc=$?
  cat "$out"
  rm -f "$out"
  ST_MESSAGE="$base"
  return $rc
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
  mkdir -p "${NAS_DIR}/${name}" 2>/dev/null || {
    log "Écriture refusée sur le disque externe (${NAS_DIR}) : la sauvegarde reste en local uniquement."
    return 1
  }
  cp "$(archive_path "$bk")" "${bk}/info.txt" "${bk}/env.backup" "${NAS_DIR}/${name}/" 2>/dev/null \
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
  [ -d "$NAS_DIR" ] || { log "Rétention ignorée : aucune copie sur le disque externe, rien n'est supprimé en local."; return 0; }
  (cd "$BACKUP_ROOT" && ls -1dt */ 2>/dev/null | tail -n +$((LOCAL_RETENTION + 1))) | while read -r old; do
    old="${old%/}"
    if [[ "$old" =~ ^[0-9]{8}_[0-9]{6}_ ]] && [ -n "$(archive_path "${NAS_DIR}/${old}")" ]; then
      log "Suppression de l'ancienne sauvegarde locale (présente sur le disque externe) : ${old}"
      rm -rf "${BACKUP_ROOT:?}/${old}"
    fi
  done
}
