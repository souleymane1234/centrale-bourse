#!/usr/bin/env python3
"""Ajoute colonnes utilisateur / parrainage (bases existantes)."""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv

load_dotenv(os.path.join(BASE_DIR, ".env"))

from storage.app_factory import create_app
from storage.models import ReferralEarning, User, db
from storage.seed import seed_subscription_plans
from storage.subscription_service import ensure_user_referral_code, generate_referral_code


def _column_exists(engine, table, column):
    from sqlalchemy import inspect

    insp = inspect(engine)
    return column in {col["name"] for col in insp.get_columns(table)}


def main():
    app = create_app()
    with app.app_context():
        engine = db.engine
        dialect = engine.dialect.name

        if dialect == "mysql":
            alters = [
                ("users", "referral_code", "VARCHAR(16) NULL UNIQUE"),
                ("users", "referred_by_user_id", "INT NULL"),
                ("users", "referral_balance_fcfa", "INT NOT NULL DEFAULT 0"),
            ]
            for table, column, ddl in alters:
                if not _column_exists(engine, table, column):
                    from sqlalchemy import text

                    db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
                    print(f"✅ {table}.{column}")
            db.session.commit()
        else:
            db.create_all()
        seed_subscription_plans()

        for user in User.query.filter(User.referral_code.is_(None)).all():
            user.referral_code = generate_referral_code()
        db.session.commit()

        for user in User.query.all():
            ensure_user_referral_code(user)

        print("✅ Migration billing / parrainage terminée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
