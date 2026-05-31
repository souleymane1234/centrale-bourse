#!/usr/bin/env python3
"""Copie les données SQLite existantes vers MySQL."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from storage.app_factory import create_app
from storage.config import get_db_engine, get_sqlite_path
from storage.database import create_database
from storage.models import db
from storage.sqlite_database import SQLiteDatabase


def main():
    if get_db_engine() != "mysql":
        print("❌ Définissez DB_ENGINE=mysql dans .env")
        sys.exit(1)

    sqlite_path = get_sqlite_path()
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite introuvable : {sqlite_path}")
        sys.exit(1)

    app = create_app()
    source = SQLiteDatabase(sqlite_path)
    companies = pd.read_sql("SELECT ticker FROM companies", source.conn)

    with app.app_context():
        target = create_database()
        for ticker in companies["ticker"]:
            prices = source.get_stock_prices(ticker, days=None)
            if prices.empty:
                continue
            target.save_daily_prices(ticker, prices)
        print(f"✅ Migration terminée vers MySQL ({target.db_path})")

    source.close()


if __name__ == "__main__":
    main()
