#!/usr/bin/env bash
set -euo pipefail

# Sauvegarde complète de jalon : tag Git horodaté + archive .env / *_Data
# (hors VictoriaMetrics_Data, traité séparément par backup_victoriametrics.sh)
# vers Backups/ (local, rétention 3) et /Volumes/Sauvegardes/0_Domotique (NAS, historique complet)
#
# Usage : ./scripts/backup_jalon.sh "nom-du-jalon"
# Exemple : ./scripts/backup_jalon.sh "jalon-1-infra-de-base"

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"nom-du-jalon\"" >&2
  exit 1
fi

JALON_NAME="$1"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DATE_ONLY="$(date +%Y-%m-%d)"
SLUG="$(echo "$JALON_NAME" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')"
BACKUP_NAME="${DATE_ONLY}_${SLUG}"

LOCAL_BACKUP_DIR="${PROJECT_ROOT}/Backups"
DEST_DIR="${LOCAL_BACKUP_DIR}/${BACKUP_NAME}"
NAS_ROOT="/Volumes/Sauvegardes/0_Domotique"
NAS_JALONS_DIR="${NAS_ROOT}/jalons"
NAS_DEST_DIR="${NAS_JALONS_DIR}/${BACKUP_NAME}"
LOCAL_RETENTION=3

echo "== Sauvegarde de jalon : ${JALON_NAME} =="

# 1. Tag Git horodaté sur le commit courant
TAG=""
if git rev-parse --git-dir > /dev/null 2>&1; then
  TAG="jalon_${SLUG}_${TIMESTAMP}"
  git tag -a "$TAG" -m "Sauvegarde jalon: ${JALON_NAME} (${TIMESTAMP})"
  echo "Tag Git créé : $TAG"
else
  echo "ATTENTION : pas de dépôt Git trouvé, tag ignoré." >&2
fi

# 2. Archive locale
mkdir -p "$DEST_DIR"

if [ -f "$PROJECT_ROOT/.env" ]; then
  cp "$PROJECT_ROOT/.env" "$DEST_DIR/.env.backup"
  echo "Copié : .env"
fi

git rev-parse HEAD > "$DEST_DIR/git-commit.txt" 2>/dev/null || echo "inconnu" > "$DEST_DIR/git-commit.txt"
[ -n "$TAG" ] && echo "$TAG" > "$DEST_DIR/git-tag.txt"

for DATA_DIR in HomeAssistant_Data Grafana_Data Prometheus_Data; do
  if [ -d "$PROJECT_ROOT/$DATA_DIR" ]; then
    echo "Archivage de ${DATA_DIR}..."
    tar -czf "$DEST_DIR/${DATA_DIR}.tar.gz" -C "$PROJECT_ROOT" "$DATA_DIR"
  else
    echo "Info : ${DATA_DIR} absent, ignoré."
  fi
done

echo "Sauvegarde locale créée : $DEST_DIR"

# 3. Copie vers le disque externe "Sauvegardes"
if [ -d "$NAS_ROOT" ]; then
  mkdir -p "$NAS_DEST_DIR"
  cp -R "$DEST_DIR/." "$NAS_DEST_DIR/"
  echo "Copie sur le disque externe : $NAS_DEST_DIR"
else
  echo "ATTENTION : disque externe 'Sauvegardes' non monté (${NAS_ROOT} introuvable)." >&2
  echo "La sauvegarde reste disponible localement dans ${DEST_DIR}." >&2
  echo "Pour copier plus tard une fois le disque monté :" >&2
  echo "  mkdir -p \"${NAS_DEST_DIR}\" && cp -R \"${DEST_DIR}/.\" \"${NAS_DEST_DIR}/\"" >&2
fi

# 4. Rétention locale : ne supprimer une ancienne sauvegarde locale
#    que si elle existe déjà sur le disque externe (sécurité contre la perte de données)
echo "Application de la rétention locale (${LOCAL_RETENTION} dernières sauvegardes conservées)..."
if [ -d "$NAS_ROOT" ]; then
  cd "$LOCAL_BACKUP_DIR"
  ls -1dt */ 2>/dev/null | tail -n +$((LOCAL_RETENTION + 1)) | while read -r OLD_DIR; do
    OLD_NAME="${OLD_DIR%/}"
    if [ -d "${NAS_JALONS_DIR}/${OLD_NAME}" ]; then
      echo "Suppression locale (déjà présente sur le disque externe) : ${OLD_NAME}"
      rm -rf "${OLD_NAME}"
    else
      echo "Conservée localement (absente du disque externe) : ${OLD_NAME}"
    fi
  done
else
  echo "Rétention locale ignorée : disque externe non monté, aucune suppression par précaution."
fi

echo "== Sauvegarde de jalon terminée =="
