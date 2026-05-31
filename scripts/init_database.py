#!/usr/bin/env python3
"""Crée les tables MySQL/SQLite et insère les données de référence."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect

from storage.app_factory import create_app
from storage.config import get_db_engine
from storage.models import db
from storage.seed import seed_subscription_plans


def main():
    app = create_app()
    with app.app_context():
        uri = app.config["SQLALCHEMY_DATABASE_URI"]
        safe_uri = uri.split("@")[-1] if "@" in uri else uri
        print(f"Moteur : {get_db_engine()}")
        print(f"Cible  : {safe_uri}")
        try:
            db.create_all()
            created = seed_subscription_plans()
            table_names = inspect(db.engine).get_table_names()
            print(f"✅ Tables créées ({len(table_names)}) :")
            for name in sorted(table_names):
                print(f"   - {name}")
            print(f"✅ Plans d'abonnement ajoutés : {created}")
        except Exception as exc:
            print(f"❌ Erreur : {exc}")
            print("\nVérifiez .env (copiez .env.example) : MYSQL_HOST, PORT, USER, PASSWORD, DATABASE")
            raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
