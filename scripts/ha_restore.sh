#!/bin/bash
# Restauration manuelle de Home Assistant à partir d'une sauvegarde faite par ha_update.sh
# (03.10.2026) — pour revenir en arrière quand un problème n'apparaît que plusieurs jours après
# une mise à jour (le retour arrière automatique ne couvre que « HA ne démarre plus »).
#
# Usage : ./scripts/ha_restore.sh                 liste les sauvegardes disponibles
#         ./scripts/ha_restore.sh <nom-du-dossier> restaure celle-ci (demande confirmation)
#
# Remet les données ET la version de Home Assistant de la sauvegarde. Tout ce que HA a
# enregistré depuis cette sauvegarde est mis de côté dans le dossier de la sauvegarde
# (HomeAssistant_Data.avant_restauration_*), rien n'est supprimé.

set -u

# shellcheck source=scripts/ha_update_lib.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/ha_update_lib.sh"

if [ $# -lt 1 ]; then
  echo "Sauvegardes disponibles dans ${BACKUP_ROOT} :"
  found=0
  for d in "$BACKUP_ROOT"/*/; do
    [ -f "${d}info.txt" ] || continue
    found=1
    echo "  $(basename "$d")   (version $(sed -n 's/^from=//p' "${d}info.txt"), $(du -sh "$(archive_path "${d%/}")" 2>/dev/null | awk '{print $1}'))"
  done
  [ "$found" -eq 1 ] || echo "  (aucune)"
  echo
  echo "Pour restaurer : $0 <nom-du-dossier>"
  exit 0
fi

BK="${BACKUP_ROOT}/$(basename "$1")"
ARCHIVE="$(archive_path "$BK")"
[ -n "$ARCHIVE" ] && [ -f "${BK}/info.txt" ] || { echo "Sauvegarde introuvable ou incomplète : ${BK}" >&2; exit 1; }

VERSION="$(sed -n 's/^from=//p' "${BK}/info.txt" | head -n 1)"
valid_version "$VERSION" || { echo "Version illisible dans ${BK}/info.txt" >&2; exit 1; }
CURRENT="$(installed_version)"

echo "Restauration de Home Assistant :"
echo "  version actuelle  : ${CURRENT:-inconnue}"
echo "  version restaurée : ${VERSION}"
echo "  sauvegarde        : ${BK}"
echo "Home Assistant sera arrêté quelques minutes. Les données actuelles sont mises de côté, pas supprimées."
printf "Confirmer ? (oui/non) "
read -r answer
[ "$answer" = "oui" ] || { echo "Annulé."; exit 0; }

mkdir -p "$STATE_DIR"
acquire_lock || { echo "Une mise à jour ou une restauration est déjà en cours." >&2; exit 3; }
trap 'release_lock' EXIT

docker info >/dev/null 2>&1 || { echo "Docker ne répond pas." >&2; exit 1; }
tar -tf "$ARCHIVE" >/dev/null || { echo "Archive illisible : rien n'a été modifié." >&2; exit 1; }
if ! docker image inspect "${HA_IMAGE_REPO}:${VERSION}" >/dev/null 2>&1; then
  echo "Téléchargement de l'image ${VERSION}…"
  docker pull "${HA_IMAGE_REPO}:${VERSION}" || { echo "Image ${VERSION} indisponible : rien n'a été modifié." >&2; exit 1; }
fi

ST_FROM="${CURRENT}"
ST_TO="${VERSION}"
ST_BACKUP="Backups/ha_update/$(basename "$BK")"
ST_STARTED="$(now_utc)"

write_status "running" "rollback" "Restauration manuelle de la version ${VERSION} en cours."
dc stop -t 120 "$HA_SERVICE"

ASIDE="${BK}/${HA_DATA_NAME}.avant_restauration_$(date +%Y%m%d_%H%M%S)"
if ! mv "$HA_DATA_DIR" "$ASIDE"; then
  dc up -d "$HA_SERVICE"
  write_status "failed" "rollback" "Restauration annulée : le dossier de données n'a pas pu être mis de côté. Home Assistant relancé tel quel."
  exit 1
fi
if ! tar -xf "$ARCHIVE" -C "$PROJECT_ROOT"; then
  rm -rf "${HA_DATA_DIR:?}" 2>/dev/null
  mv "$ASIDE" "$HA_DATA_DIR"
  dc up -d "$HA_SERVICE"
  write_status "failed" "rollback" "Restauration annulée : archive illisible. Home Assistant relancé avec ses données actuelles."
  exit 1
fi

set_image_tag "$VERSION"
dc up -d "$HA_SERVICE"
echo "Démarrage de Home Assistant ${VERSION}, vérification en cours (quelques minutes)…"
if wait_for_ha "$VERSION" "$HA_ROLLBACK_TIMEOUT"; then
  dc restart dashboard-api >/dev/null 2>&1
  write_status "rolled_back" "rollback" "Restauration manuelle terminée : Home Assistant est revenu en ${VERSION}."
  echo "Terminé. Données d'avant restauration conservées dans : ${ASIDE}"
  exit 0
fi

dc restart dashboard-api >/dev/null 2>&1
write_status "failed" "rollback" "Restauration effectuée mais Home Assistant ${VERSION} ne répond pas. Voir : docker logs --tail 50 homeassistant"
exit 1
