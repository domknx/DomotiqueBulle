#!/bin/bash
# Agent côté Mac de la page « Version » du dashboard (03.10.2026).
#
# Lancé par launchd toutes les minutes et dès qu'un fichier apparaît dans
# dashboard/version/state/requests/ (voir scripts/install_ha_update_agent.sh). Son rôle :
#   - écrire un témoin de présence, pour que la page sache que le bouton peut fonctionner ;
#   - signaler une mise à jour interrompue (Mac redémarré en cours de route) ;
#   - ramasser une demande de mise à jour déposée par dashboard-api et lancer ha_update.sh.
#
# C'est le seul point de passage entre le dashboard (web) et Docker : dashboard-api n'a aucun
# accès au socket Docker, il ne sait que déposer un fichier de demande ici.

set -u

# shellcheck source=scripts/ha_update_lib.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/ha_update_lib.sh"

mkdir -p "$REQ_DIR"
touch_heartbeat

# Mise à jour interrompue : l'état dit « en cours » mais plus aucun script ne tourne.
if grep -q '^state=running$' "$STATUS_FILE" 2>/dev/null && { [ ! -d "$LOCK_DIR" ] || lock_is_stale; }; then
  ST_FROM="$(sed -n 's/^from=//p' "$STATUS_FILE" | head -n 1)"
  ST_TO="$(sed -n 's/^to=//p' "$STATUS_FILE" | head -n 1)"
  ST_BACKUP="$(sed -n 's/^backup=//p' "$STATUS_FILE" | head -n 1)"
  ST_STARTED="$(sed -n 's/^started_at=//p' "$STATUS_FILE" | head -n 1)"
  release_lock
  write_status "failed" "interrupted" "Mise à jour interrompue avant la fin (Mac redémarré ?). Home Assistant est peut-être arrêté : voir scripts/ha_restore.sh, ou relancer avec « docker compose up -d homeassistant »." >> "$LOG_FILE" 2>&1
fi

REQ="${REQ_DIR}/update_request"
[ -f "$REQ" ] || exit 0

# Un script est déjà en cours : la demande attend le prochain passage.
if [ -d "$LOCK_DIR" ] && ! lock_is_stale; then exit 0; fi

VERSION="$(sed -n 's/^version=//p' "$REQ" | head -n 1 | tr -d '[:space:]')"
# La demande est retirée de la file avant tout traitement : elle ne sera jamais rejouée.
mv -f "$REQ" "${STATE_DIR}/last_request"

if ! valid_version "$VERSION"; then
  ST_STARTED="$(now_utc)"
  write_status "failed" "checks" "Demande de mise à jour invalide, ignorée." >> "$LOG_FILE" 2>&1
  exit 1
fi

exec "${PROJECT_ROOT}/scripts/ha_update.sh" "$VERSION"
