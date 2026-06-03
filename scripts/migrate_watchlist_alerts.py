#!/usr/bin/env python3
"""Crée les tables user_watchlist et user_price_alerts."""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv

load_dotenv(os.path.join(BASE_DIR, ".env"))

from storage.app_factory import create_app
from storage.models import UserPriceAlert, UserWatchlistItem, db


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✅ Tables watchlist / alertes prêtes.")
        print(f"   - {UserWatchlistItem.__tablename__}")
        print(f"   - {UserPriceAlert.__tablename__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
