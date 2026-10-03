#!/bin/bash
# Sauvegarde puis mise à jour de Home Assistant vers une version précise, avec retour arrière
# automatique si la nouvelle version ne démarre pas (03.10.2026).
#
# Usage : ./scripts/ha_update.sh 2026.9.4
#         ./scripts/ha_update.sh --dry-run 2026.9.4   (contrôles seulement, ne touche à rien)
#
# Lancé normalement par l'agent launchd (scripts/ha_update_agent.sh) quand le bouton
# « Sauvegarder et mettre à jour » de la page Version du dashboard est pressé ; peut aussi être
# lancé à la main dans le Terminal. Déroulé :
#   1. contrôles (Docker, versions, place disque) ;
#   2. téléchargement de la nouvelle image — HA tourne encore, rien n'est modifié si ça échoue ;
#   3. arrêt de HA, archive complète de HomeAssistant_Data dans Backups/ha_update/ (non
#      compressée à ce stade : plus rapide, et compressée une fois HA reparti) ;
#   4. démarrage de la nouvelle version (HA_IMAGE_TAG dans .env) ;
#   5. vérification : conteneur démarré, interface joignable, bonne version, encore là 60 s après ;
#   6. en cas d'échec : restauration de l'archive et redémarrage de l'ancienne version.
# L'avancement est écrit dans dashboard/version/state/update_status (lu par la page), avec deux
# pourcentages réels : backup_pct (taille de l'archive écrite) et update_pct (jalons constatés du
# démarrage de la nouvelle version, puis décompte du contrôle de stabilité). Le détail est
# dans dashboard/version/state/update.log.

set -u

# shellcheck source=scripts/ha_update_lib.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/ha_update_lib.sh"

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then DRY_RUN=1; shift; fi
TARGET="${1:-}"

if ! valid_version "$TARGET"; then
  echo "Usage : $0 [--dry-run] <version>   (ex. $0 2026.9.4)" >&2
  exit 2
fi

mkdir -p "$STATE_DIR" "$REQ_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

if ! acquire_lock; then
  log "Une mise à jour ou une restauration est déjà en cours : abandon."
  exit 3
fi
trap 'release_lock' EXIT

ST_TO="$TARGET"
ST_STARTED="$(now_utc)"
BK=""

fail() { write_status "failed" "$1" "$2"; exit 1; }

# Retour arrière : remet les données sauvegardées et l'ancienne version. $1 = raison de l'échec.
rollback() {
  local reason="$1" failed_copy
  write_status "running" "rollback" "Échec (${reason}). Retour à la version ${ST_FROM} en cours."
  dc stop -t 120 "$HA_SERVICE"
  failed_copy="${BK}/${HA_DATA_NAME}.apres_echec"
  if ! mv "$HA_DATA_DIR" "$failed_copy"; then
    fail "rollback" "Retour arrière impossible : le dossier de données n'a pas pu être mis de côté. Sauvegarde intacte dans ${ST_BACKUP}. Voir scripts/ha_restore.sh."
  fi
  if ! tar -xf "$(archive_path "$BK")" -C "$PROJECT_ROOT"; then
    fail "rollback" "Retour arrière impossible : l'archive n'a pas pu être restaurée. Les données d'après mise à jour sont dans ${failed_copy}."
  fi
  set_image_tag "$ST_FROM" || fail "rollback" "Retour arrière incomplet : .env n'a pas pu être corrigé (HA_IMAGE_TAG=${ST_FROM})."
  dc up -d "$HA_SERVICE"
  if wait_for_ha "$ST_FROM" "$HA_ROLLBACK_TIMEOUT"; then
    dc restart dashboard-api >/dev/null 2>&1
    write_status "rolled_back" "rollback" "La version ${ST_TO} n'a pas démarré correctement (${reason}). Home Assistant est revenu en ${ST_FROM}, données restaurées."
    exit 1
  fi
  dc restart dashboard-api >/dev/null 2>&1
  fail "rollback" "Retour arrière effectué mais Home Assistant ${ST_FROM} ne répond pas. Vérifier avec : docker logs --tail 50 homeassistant"
}

log "===== Mise à jour de Home Assistant vers ${TARGET} ====="

# ---- 1. Contrôles ---------------------------------------------------------------------------
write_status "running" "checks" "Contrôles avant mise à jour."

docker info >/dev/null 2>&1 || fail "checks" "Docker ne répond pas sur le Mac mini. Rien n'a été modifié."
docker inspect "$HA_CONTAINER" >/dev/null 2>&1 || fail "checks" "Conteneur ${HA_CONTAINER} introuvable. Rien n'a été modifié."

ST_FROM="$(installed_version)"
valid_version "$ST_FROM" || fail "checks" "Version installée illisible (${HA_DATA_NAME}/.HA_VERSION). Rien n'a été modifié."
version_gt "$TARGET" "$ST_FROM" || fail "checks" "La version ${TARGET} n'est pas plus récente que la version installée (${ST_FROM}). Rien n'a été modifié."

DATA_KB="$(du -sk "$HA_DATA_DIR" | awk '{print $1}')"
FREE_KB="$(df -k "$PROJECT_ROOT" | awk 'NR==2 {print $4}')"
NEED_KB=$((DATA_KB * 2 + 1048576))
if [ -z "$FREE_KB" ] || [ "$FREE_KB" -lt "$NEED_KB" ]; then
  fail "checks" "Place disque insuffisante pour la sauvegarde (libre : $((${FREE_KB:-0} / 1024)) Mo, nécessaire : $((NEED_KB / 1024)) Mo). Rien n'a été modifié."
fi

# ---- 2. Téléchargement (HA tourne encore) ----------------------------------------------------
write_status "running" "pull" "Téléchargement de Home Assistant ${TARGET}."
pull_with_progress "${HA_IMAGE_REPO}:${TARGET}" || fail "pull" "Téléchargement de l'image ${TARGET} impossible. Home Assistant n'a pas été touché."

# L'image actuelle est étiquetée avec son numéro de version, pour pouvoir y revenir même si
# l'étiquette « stable » a bougé entre-temps.
OLD_IMAGE_ID="$(docker inspect -f '{{.Image}}' "$HA_CONTAINER")"
if ! docker image inspect "${HA_IMAGE_REPO}:${ST_FROM}" >/dev/null 2>&1; then
  docker tag "$OLD_IMAGE_ID" "${HA_IMAGE_REPO}:${ST_FROM}" \
    || fail "pull" "Impossible de conserver l'image de la version ${ST_FROM}. Home Assistant n'a pas été touché."
fi

if [ "$DRY_RUN" -eq 1 ]; then
  write_status "idle" "" "Essai à blanc réussi : ${ST_FROM} vers ${TARGET}, image téléchargée, rien n'a été modifié."
  exit 0
fi

# ---- 3. Arrêt et sauvegarde ------------------------------------------------------------------
write_status "running" "stop" "Arrêt de Home Assistant ${ST_FROM}."
dc stop -t 120 "$HA_SERVICE" || fail "stop" "Home Assistant n'a pas pu être arrêté. Rien n'a été modifié."

BK="${BACKUP_ROOT}/$(date +%Y%m%d_%H%M%S)_${ST_FROM}_vers_${TARGET}"
ST_BACKUP="Backups/ha_update/$(basename "$BK")"
write_status "running" "backup" "Sauvegarde complète de ${HA_DATA_NAME}."

backup_failed() {
  dc up -d "$HA_SERVICE"
  fail "backup" "$1 Home Assistant ${ST_FROM} a été relancé tel quel."
}

mkdir -p "$BK" || backup_failed "Dossier de sauvegarde impossible à créer."
backup_with_progress "${BK}/${HA_DATA_NAME}.tar" || backup_failed "L'archive de sauvegarde a échoué ou est illisible."
cp "$ENV_FILE" "${BK}/env.backup" && chmod 600 "${BK}/env.backup"
{
  echo "date=$(now_utc)"
  echo "from=${ST_FROM}"
  echo "to=${TARGET}"
  echo "image_from=${OLD_IMAGE_ID}"
  echo "git_commit=$(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo inconnu)"
} > "${BK}/info.txt"
log "Sauvegarde créée : ${BK} ($(du -sh "${BK}/${HA_DATA_NAME}.tar" | awk '{print $1}'))"

# ---- 4. Mise à jour --------------------------------------------------------------------------
write_status "running" "update" "Démarrage de Home Assistant ${TARGET}."
set_progress update 5
set_image_tag "$TARGET" || rollback "le fichier .env n'a pas pu être modifié"
dc up -d "$HA_SERVICE" || rollback "le conteneur n'a pas pu être recréé"

# ---- 5. Vérification -------------------------------------------------------------------------
write_status "running" "verify" "Vérification du démarrage (migration de la base possible, jusqu'à 15 minutes)."
wait_for_ha "$TARGET" "$HA_VERIFY_TIMEOUT" progress || rollback "pas de réponse correcte dans le délai imparti"

# dashboard-api lit .HA_VERSION par un montage de fichier : on vérifie qu'il voit la nouvelle valeur.
if [ "$(docker exec dashboard-api cat /ha/HA_VERSION 2>/dev/null | tr -d '[:space:]')" != "$TARGET" ]; then
  dc restart dashboard-api >/dev/null 2>&1
fi

write_status "success" "done" "Home Assistant est passé de ${ST_FROM} à ${TARGET}. Sauvegarde conservée dans ${ST_BACKUP}."

# ---- 6. Compression, copie externe et rétention (sans incidence sur le résultat) --------------
gzip "${BK}/${HA_DATA_NAME}.tar" || log "Compression de l'archive impossible : elle reste au format .tar."
copy_backup_to_nas "$BK"
apply_retention
log "===== Terminé ====="
exit 0
