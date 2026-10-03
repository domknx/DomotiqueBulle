#!/bin/bash
# Installe (ou désinstalle) l'agent launchd qui exécute les mises à jour de Home Assistant
# demandées depuis la page « Version » du dashboard (03.10.2026).
#
# Usage : ./scripts/install_ha_update_agent.sh            installe ou réinstalle
#         ./scripts/install_ha_update_agent.sh uninstall  désinstalle
#
# À lancer une seule fois, dans le Terminal du Mac mini, avec le compte qui fait tourner
# Docker Desktop. L'agent tourne dans la session de ce compte (LaunchAgent) : il n'est actif
# que lorsque ce compte est connecté, comme Docker Desktop lui-même.

set -eu

# shellcheck source=scripts/ha_update_lib.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/ha_update_lib.sh"

LABEL="com.villabulle.ha-update"
PLIST="${HOME}/Library/LaunchAgents/${LABEL}.plist"
DOMAIN="gui/$(id -u)"

if [ "$(uname)" != "Darwin" ]; then
  echo "Ce script s'exécute sur le Mac mini (macOS), pas ici." >&2
  exit 1
fi

launchctl bootout "${DOMAIN}/${LABEL}" 2>/dev/null || true

if [ "${1:-}" = "uninstall" ]; then
  rm -f "$PLIST" "$HEARTBEAT_FILE"
  echo "Agent désinstallé. Le bouton de mise à jour du dashboard est désormais inactif."
  exit 0
fi

command -v docker >/dev/null 2>&1 || { echo "Commande docker introuvable : Docker Desktop est-il installé ?" >&2; exit 1; }

mkdir -p "$REQ_DIR" "${HOME}/Library/LaunchAgents"
chmod +x "${PROJECT_ROOT}/scripts/ha_update.sh" "${PROJECT_ROOT}/scripts/ha_update_agent.sh" \
         "${PROJECT_ROOT}/scripts/ha_restore.sh" "${PROJECT_ROOT}/scripts/ha_update_lib.sh"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${PROJECT_ROOT}/scripts/ha_update_agent.sh</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${PROJECT_ROOT}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>StartInterval</key>
  <integer>60</integer>
  <key>WatchPaths</key>
  <array>
    <string>${REQ_DIR}</string>
  </array>
  <key>ProcessType</key>
  <string>Background</string>
  <key>StandardOutPath</key>
  <string>${STATE_DIR}/agent.log</string>
  <key>StandardErrorPath</key>
  <string>${STATE_DIR}/agent.log</string>
</dict>
</plist>
EOF

launchctl bootstrap "$DOMAIN" "$PLIST"

echo "Agent installé (${PLIST}). Vérification…"
sleep 4
if [ -f "$HEARTBEAT_FILE" ]; then
  echo "OK : l'agent répond (témoin : $(cat "$HEARTBEAT_FILE"))."
  echo "Le bouton « Sauvegarder et mettre à jour » de la page Version est maintenant actif."
else
  echo "ATTENTION : l'agent ne s'est pas manifesté. Voir ${STATE_DIR}/agent.log" >&2
  exit 1
fi
