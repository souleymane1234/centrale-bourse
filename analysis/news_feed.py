"""Chargement et sérialisation du fil d'actualités BRVM."""

import json
import os
import re
import unicodedata
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWS_DATA_PATH = os.path.join(BASE_DIR, "data", "news_articles.json")

BADGE_LABELS = {
    "marche": "Marché",
    "brvm": "BRVM",
    "societe": "Société",
    "dividende": "Dividende",
    "communique": "Communiqué",
    "obligation": "Obligations",
}

_payload_cache = None


def _slugify(text):
    if not text:
        return "article"
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:120] or "article"


def load_news_payload():
    global _payload_cache
    if _payload_cache is not None:
        return _payload_cache

    if not os.path.exists(NEWS_DATA_PATH):
        _payload_cache = {"generated_at": None, "articles": []}
        return _payload_cache

    with open(NEWS_DATA_PATH, "r", encoding="utf-8") as file:
        _payload_cache = json.load(file)
    return _payload_cache


def invalidate_news_cache():
    global _payload_cache
    _payload_cache = None


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


def _ensure_article_ids(articles):
    seen = set()
    for index, article in enumerate(articles):
        slug = article.get("slug") or _slugify(article.get("title"))
        base = slug
        counter = 2
        while slug in seen:
            slug = f"{base}-{counter}"
            counter += 1
        seen.add(slug)
        article["slug"] = slug
        article["id"] = article.get("id") or slug
        badge_key = (article.get("badge") or "brvm").lower()
        article["badge_label"] = BADGE_LABELS.get(badge_key, article.get("badge") or "BRVM")
    return articles


def get_all_articles():
    payload = load_news_payload()
    articles = _ensure_article_ids(list(payload.get("articles") or []))
    articles.sort(
        key=lambda item: _parse_datetime(item.get("published_at")) or datetime.min.replace(
            tzinfo=timezone.utc
        ),
        reverse=True,
    )
    return articles


def get_article_by_slug(slug):
    if not slug:
        return None
    normalized = _slugify(slug)
    for article in get_all_articles():
        if article.get("slug") == normalized or article.get("id") == normalized:
            return article
    return None


def serialize_feed_item(article):
    """Résumé pour la carte du fil (type réseau social)."""
    media_type = article.get("media_type") or ("video" if article.get("video_url") else "image")
    return {
        "id": article.get("id"),
        "slug": article.get("slug"),
        "title": article.get("title"),
        "excerpt": article.get("excerpt") or "",
        "badge": article.get("badge_label"),
        "badge_key": (article.get("badge") or "brvm").lower(),
        "media_type": media_type if article.get("image_url") or article.get("video_url") else None,
        "image_url": article.get("image_url"),
        "video_url": article.get("video_url"),
        "thumbnail_url": article.get("thumbnail_url") or article.get("image_url"),
        "source": article.get("source") or "BRVM",
        "source_url": article.get("source_url"),
        "published_at": article.get("published_at"),
        "ticker": article.get("ticker"),
        "author": article.get("author"),
    }


def serialize_article_detail(article):
    """Article complet pour la page détail."""
    item = serialize_feed_item(article)
    item["body"] = article.get("body") or ""
    item["body_html"] = article.get("body_html") or ""
    return item


def list_feed(page=1, per_page=12):
    page = max(1, int(page or 1))
    per_page = max(1, min(50, int(per_page or 12)))
    articles = get_all_articles()
    total = len(articles)
    start = (page - 1) * per_page
    end = start + per_page
    items = [serialize_feed_item(article) for article in articles[start:end]]
    return {
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "has_more": end < total,
        "generated_at": load_news_payload().get("generated_at"),
    }
