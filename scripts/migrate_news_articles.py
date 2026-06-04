"""Synchronise les actualités scrapées / JSON vers la table news_articles."""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv

load_dotenv(os.path.join(BASE_DIR, ".env"))

from storage.app_factory import create_app
from storage.models import NewsArticle, db
from storage.news_store import import_from_json


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        imported = import_from_json()
        total = NewsArticle.query.count()
        active = NewsArticle.query.filter_by(is_active=True).count()
        print(f"✅ Table news_articles prête.")
        print(f"   Import JSON : {imported} article(s) traités.")
        print(f"   Total en base : {total} ({active} actifs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
