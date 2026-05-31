#!/usr/bin/env python3
"""Importe les cotations du dataset JSON dans la base SQLite."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.app_factory import create_app
from storage.database import create_database
from storage.price_sync import backfill_from_json_file

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "companies_full.json",
)


def main():
    if not os.path.exists(DATA_PATH):
        print(f"❌ Fichier introuvable : {DATA_PATH}")
        sys.exit(1)

    app = create_app()
    with app.app_context():
        database = create_database()
        synced, listed_count = backfill_from_json_file(db=database, json_path=DATA_PATH)
        companies_in_db = database.count_companies() if hasattr(database, "count_companies") else "?"
        print(f"✅ {listed_count} sociétés cotées Sikafinance → {synced} cours du jour")
        print(f"✅ {companies_in_db} lignes dans la table companies ({database.db_path})")
        database.close()


if __name__ == "__main__":
    main()
