#!/usr/bin/env bash
set -euo pipefail

# Sauvegarde hebdomadaire de VictoriaMetrics (snapshot natif), INDEPENDANTE des jalons du projet
# (les données de séries temporelles évoluent en continu, cadence propre — voir CLAUDE.md §10.3)
#
# Usage : ./scripts/backup_victoriametrics.sh

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
NAS_ROOT="/Volumes/Sauvegardes/0_Domotique"
NAS_VM_DIR="${NAS_ROOT}/victoriametrics"

echo "== Sauvegarde VictoriaMetrics (${TIMESTAMP}) =="

if ! curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8428/health | grep -q "200"; then
  echo "ERREUR : VictoriaMetrics ne répond pas sur http://127.0.0.1:8428 (conteneur démarré ?)" >&2
  exit 1
fi

# 1. Créer un snapshot via l'API native de VictoriaMetrics (accès local uniquement, port 8428)
SNAPSHOT_RESPONSE="$(curl -s http://127.0.0.1:8428/snapshot/create)"
echo "Réponse API snapshot : $SNAPSHOT_RESPONSE"

SNAPSHOT_NAME="$(echo "$SNAPSHOT_RESPONSE" | grep -o '"snapshot":"[^"]*"' | cut -d'"' -f4)"

if [ -z "$SNAPSHOT_NAME" ]; then
  echo "ERREUR : impossible de créer le snapshot (réponse inattendue)." >&2
  exit 1
fi

echo "Snapshot créé : $SNAPSHOT_NAME"
SNAPSHOT_PATH="${PROJECT_ROOT}/VictoriaMetrics_Data/snapshots/${SNAPSHOT_NAME}"

# 2. Copier le snapshot vers le disque externe "Sauvegardes"
if [ -d "$NAS_ROOT" ]; then
  DEST="${NAS_VM_DIR}/${TIMESTAMP}"
  mkdir -p "$DEST"
  cp -R "${SNAPSHOT_PATH}/." "$DEST/"
  echo "Snapshot copié vers : $DEST"

  # 3. Nettoyage du snapshot local (déjà copié sur le disque externe, ne pas accumuler dans VictoriaMetrics_Data)
  DELETE_RESPONSE="$(curl -s -X POST "http://127.0.0.1:8428/snapshot/delete?snapshot=${SNAPSHOT_NAME}")"
  echo "Nettoyage du snapshot local : $DELETE_RESPONSE"
else
  echo "ATTENTION : disque externe 'Sauvegardes' non monté (${NAS_ROOT} introuvable)." >&2
  echo "Le snapshot reste local dans ${SNAPSHOT_PATH} — à copier manuellement une fois le disque monté, puis supprimer via :" >&2
  echo "  curl -s -X POST \"http://127.0.0.1:8428/snapshot/delete?snapshot=${SNAPSHOT_NAME}\"" >&2
fi

# NOTE : politique de rétention côté disque externe pas encore définie (à ajuster une fois
# le volume réel de données observé sur quelques semaines) — voir CLAUDE.md §10.3.

echo "== Sauvegarde VictoriaMetrics terminée =="
