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


def main():
    limit = int(os.getenv("NEWS_SCRAPE_LIMIT", "20"))
    payload = scrape_brvm_news(limit=limit)
    invalidate_news_cache()
    print(f"✅ {len(payload.get('articles') or [])} actualités → data/news_articles.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
