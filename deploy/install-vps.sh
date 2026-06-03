#!/bin/bash
# Installation guidée sur VPS — à lancer depuis la racine du projet
# Usage : bash deploy/install-vps.sh
# Prérequis : MySQL et Redis déjà accessibles, ou ports libres pour Docker

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== Centrale Bourse — préparation VPS ==="

if [[ ! -f .env ]]; then
  if [[ -f deploy/env.preprod.example ]]; then
    cp deploy/env.preprod.example .env
    echo "→ Fichier .env créé depuis deploy/env.preprod.example — remplacez IP_DU_VPS et les mots de passe."
  elif [[ -f deploy/env.production.example ]]; then
    cp deploy/env.production.example .env
    echo "→ Fichier .env créé depuis deploy/env.production.example — ÉDITEZ-LE avant la prod."
  else
    cp .env.api.example .env
    echo "→ Fichier .env créé — ÉDITEZ-LE."
  fi
fi

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "→ Initialisation base de données..."
python scripts/init_database.py
python scripts/migrate_user_billing.py 2>/dev/null || true
python scripts/migrate_watchlist_alerts.py 2>/dev/null || true

if command -v npm >/dev/null 2>&1; then
  echo "→ Build frontend..."
  cd frontend
  npm ci
  npm run build
  cd ..
else
  echo "⚠️  npm absent : lancez plus tard « cd frontend && npm ci && npm run build »"
fi

mkdir -p logs
echo ""
echo "✅ Préparation terminée."
echo "   1. Éditez .env (MySQL, Redis /2, SECRET_KEY, CORS_ORIGINS, GUNICORN_BIND=127.0.0.1:5051)"
echo "   2. sudo cp deploy/centrale-bourse-api.service /etc/systemd/system/ (adapter User/WorkingDirectory)"
echo "   3. Pré-prod sans domaine : deploy/nginx-preprod.conf.example (port 8080)"
echo "   4. Voir docs/DEPLOIEMENT_PREPROD_UBUNTU.md"
