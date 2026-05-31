#!/usr/bin/env python3
"""Importe l'historique des cours depuis Sikafinance (graphiques réels)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.app_factory import create_app
from storage.database import create_database
from storage.price_sync import (
    backfill_all_price_histories,
    sync_live_sikafinance_listing,
)


def build_listed_companies(database):
    """Liste des 48 sociétés cotées (même logique que l'API)."""
    synced, _ = sync_live_sikafinance_listing(db=database)
    print(f"Cotations du jour synchronisées : {synced}")

    from app import get_listed_company_records

    return get_listed_company_records()


def main():
    app = create_app()
    with app.app_context():
        database = create_database()
        print("📥 Récupération de la liste des sociétés cotées…")
        companies = build_listed_companies(database)
        print(f"📊 Import historique Sikafinance pour {len(companies)} sociétés…")

        success, total_sessions = backfill_all_price_histories(companies, db=database)
        print(
            f"\n✅ Terminé : {success}/{len(companies)} sociétés, "
            f"{total_sessions} séances enregistrées."
        )
        print(f"   Base : {database.db_path}")
        database.close()


if __name__ == "__main__":
    main()
