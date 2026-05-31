#!/usr/bin/env python3
"""
Worker scrape longue durée (processus séparé de l'API).

Lance un scrape complet toutes les SCRAPE_INTERVAL_HOURS (défaut 2 h),
hors week-end BRVM, puis invalide + pré-chauffe le cache API.

Usage :
  python scripts/run_scrape_worker.py

En production, l'API doit avoir DISABLE_SCRAPE_SCHEDULER=true.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv

load_dotenv(os.path.join(BASE_DIR, ".env"))

from jobs.env_worker import apply_worker_env

apply_worker_env()

from jobs.company_data_refresh import run_scrape_worker_forever
from jobs.post_scrape import run_post_scrape_hooks


def main():
    print("🚀 Worker scrape BRVM (processus dédié)")
    print(f"   SCRAPE_INTERVAL_HOURS={os.getenv('SCRAPE_INTERVAL_HOURS', '2')}")
    print(f"   WARM_CACHE_AFTER_SCRAPE={os.getenv('WARM_CACHE_AFTER_SCRAPE', 'true')}")
    run_scrape_worker_forever(on_complete=run_post_scrape_hooks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
