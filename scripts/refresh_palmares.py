#!/usr/bin/env python3
"""
Rafraîchit le palmarès Sikafinance (Top hausses / baisses).

- Lun–ven : fetch live + snapshot data/palmares_snapshot.json
- Sam–dim : aucun fetch (conserve le vendredi)

Cron recommandé (toutes les 4 h, jours ouvrés) :
  0 */4 * * 1-5 cd /chemin/brvm_agent && python3 scripts/refresh_palmares.py >> logs/palmares.log 2>&1
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv

load_dotenv(os.path.join(BASE_DIR, ".env"))

from jobs.env_worker import apply_worker_env
from jobs.palmares_refresh import run_palmares_refresh_cycle

apply_worker_env()


def main():
    ok = run_palmares_refresh_cycle()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
