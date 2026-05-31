#!/usr/bin/env python3
"""
Pré-chauffe les caches API (cotations, marché, comparer).

Usage (cron toutes les 5 min en production) :
  ALLOW_LIVE_QUOTE_FETCH=true python scripts/warm_api_cache.py

Avec l'API déjà lancée, vous pouvez aussi appeler GET /api/health puis
laisser le premier visiteur déclencher le cache — ce script évite la stampede.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv

load_dotenv(os.path.join(BASE_DIR, ".env"))

from jobs.env_worker import apply_worker_env

apply_worker_env()


def main():
    from app import app, warm_api_caches

    with app.app_context():
        warm_api_caches()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
