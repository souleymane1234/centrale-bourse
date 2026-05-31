#!/usr/bin/env python3
"""
Scrape ponctuel du dataset sociétés (BRVM + Sikafinance).

Usage :
  python scrape_companies.py
  python scrape_companies.py --force   # même le week-end
  python scrape_companies.py --no-warm # sans pré-chauffage Redis
"""

import argparse
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv

load_dotenv(os.path.join(BASE_DIR, ".env"))

from jobs.env_worker import apply_worker_env

apply_worker_env()

from jobs.company_data_refresh import run_scrape_cycle
from jobs.post_scrape import run_post_scrape_hooks


def main():
    parser = argparse.ArgumentParser(description="Scrape BRVM + Sikafinance → companies_full.json")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Lancer même samedi/dimanche (marché fermé)",
    )
    parser.add_argument(
        "--no-warm",
        action="store_true",
        help="Ne pas invalider / pré-chauffer le cache API après le scrape",
    )
    args = parser.parse_args()

    if args.no_warm:
        os.environ["SKIP_POST_SCRAPE_HOOKS"] = "1"

    on_complete = None if args.no_warm else run_post_scrape_hooks
    success = run_scrape_cycle(on_complete=on_complete, force=args.force)

    if not success:
        raise SystemExit(1)

    print("✅ Scrape terminé.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
