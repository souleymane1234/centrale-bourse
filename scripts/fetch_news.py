#!/usr/bin/env python3
"""Récupère les actualités BRVM et met à jour data/news_articles.json."""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv

load_dotenv(os.path.join(BASE_DIR, ".env"))

from analysis.news_feed import invalidate_news_cache
from collectors.brvm_news_scraper import scrape_brvm_news
from storage.news_store import sync_scraped_articles


def main():
    from storage.app_factory import create_app

    limit = int(os.getenv("NEWS_SCRAPE_LIMIT", "20"))
    payload = scrape_brvm_news(limit=limit)

    app = create_app()
    with app.app_context():
        synced = sync_scraped_articles(payload.get("articles") or [])

    invalidate_news_cache()
    print(
        f"✅ {len(payload.get('articles') or [])} actualités → JSON + {synced} en base (news_articles)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
