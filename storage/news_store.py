"""Persistance des actualités en base (table news_articles)."""

import json
import os
from datetime import datetime, timezone

from storage.models import NewsArticle, db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWS_DATA_PATH = os.path.join(BASE_DIR, "data", "news_articles.json")


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _use_database():
    return os.getenv("NEWS_USE_DATABASE", "true").lower() in ("1", "true", "yes")


def article_to_dict(row: NewsArticle):
    published = row.published_at.isoformat() if row.published_at else None
    return {
        "id": str(row.id),
        "slug": row.slug,
        "title": row.title,
        "excerpt": row.excerpt or "",
        "body": row.body or "",
        "body_html": row.body_html or "",
        "badge": row.badge or "brvm",
        "media_type": row.media_type,
        "image_url": row.image_url,
        "video_url": row.video_url,
        "thumbnail_url": row.thumbnail_url or row.image_url,
        "source": row.source or "BRVM",
        "source_url": row.source_url,
        "published_at": published,
        "ticker": row.ticker,
        "author": row.author,
        "is_active": bool(row.is_active),
    }


def count_articles(*, active_only=False):
    query = NewsArticle.query
    if active_only:
        query = query.filter_by(is_active=True)
    return query.count()


def fetch_articles(*, active_only=True):
    query = NewsArticle.query
    if active_only:
        query = query.filter_by(is_active=True)
    rows = query.order_by(
        NewsArticle.published_at.desc(),
        NewsArticle.id.desc(),
    ).all()
    return [article_to_dict(row) for row in rows]


def get_article_by_slug(slug, *, active_only=True):
    if not slug:
        return None
    query = NewsArticle.query.filter_by(slug=slug)
    if active_only:
        query = query.filter_by(is_active=True)
    row = query.first()
    return article_to_dict(row) if row else None


def upsert_article(data, *, preserve_active=True):
    slug = (data.get("slug") or "").strip()
    if not slug:
        raise ValueError("Slug d'actualité requis.")

    row = NewsArticle.query.filter_by(slug=slug).first()
    creating = row is None
    if creating:
        row = NewsArticle(slug=slug)
        db.session.add(row)

    if creating:
        row.is_active = bool(data.get("is_active", True))
    elif "is_active" in data:
        row.is_active = bool(data["is_active"])
    elif not preserve_active:
        row.is_active = bool(data.get("is_active", True))

    row.title = (data.get("title") or slug).strip()
    row.excerpt = data.get("excerpt")
    row.body = data.get("body")
    row.body_html = data.get("body_html")
    row.badge = (data.get("badge") or "brvm").lower()
    row.media_type = data.get("media_type")
    row.image_url = data.get("image_url")
    row.video_url = data.get("video_url")
    row.thumbnail_url = data.get("thumbnail_url")
    row.source = data.get("source")
    row.source_url = data.get("source_url")
    row.published_at = _parse_datetime(data.get("published_at")) or row.published_at or datetime.now(
        timezone.utc
    )
    row.ticker = data.get("ticker")
    row.author = data.get("author")
    row.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return row


def sync_scraped_articles(articles):
    synced = 0
    for payload in articles or []:
        upsert_article(payload, preserve_active=True)
        synced += 1
    return synced


def import_from_json(path=None, *, default_active=True):
    path = path or NEWS_DATA_PATH
    if not os.path.exists(path):
        return 0

    with open(path, "r", encoding="utf-8") as file:
        payload = json.load(file)

    imported = 0
    for item in payload.get("articles") or []:
        item = dict(item)
        if default_active and "is_active" not in item:
            item["is_active"] = True
        upsert_article(item, preserve_active=False)
        imported += 1
    return imported


def set_article_active(slug, is_active):
    row = NewsArticle.query.filter_by(slug=slug).first()
    if not row:
        raise ValueError("Actualité introuvable.")
    row.is_active = bool(is_active)
    row.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return article_to_dict(row)


def latest_updated_at():
    row = NewsArticle.query.order_by(NewsArticle.updated_at.desc()).first()
    return row.updated_at.isoformat() if row and row.updated_at else None


def load_articles_for_feed(*, active_only=True):
    """Charge depuis la base si disponible, sinon retourne None (fallback JSON)."""
    if not _use_database():
        return None
    try:
        if count_articles() == 0:
            return None
        return fetch_articles(active_only=active_only)
    except Exception:
        return None
