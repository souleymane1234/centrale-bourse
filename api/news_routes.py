"""API fil d'actualités."""

from flask import Blueprint, jsonify, request

from analysis.news_feed import get_article_by_slug, invalidate_news_cache, list_feed, serialize_article_detail

news_bp = Blueprint("news", __name__, url_prefix="/api/news")


def _require_news_admin():
    admin_key = request.headers.get("X-Admin-Key") or request.args.get("admin_key")
    expected = __import__("os").getenv("NEWS_REFRESH_ADMIN_KEY", "")
    if expected and admin_key != expected:
        return jsonify({"error": "Non autorisé."}), 403
    return None


@news_bp.get("")
def news_feed():
    """Liste paginée pour le fil (cartes type réseau social)."""
    page = request.args.get("page", 1)
    per_page = request.args.get("per_page", 12)
    return jsonify(list_feed(page=page, per_page=per_page))


@news_bp.get("/<slug>")
def news_detail(slug):
    """Détail d'une actualité."""
    article = get_article_by_slug(slug)
    if not article:
        return jsonify({"error": "Actualité introuvable."}), 404
    return jsonify(serialize_article_detail(article))


@news_bp.post("/refresh")
def news_refresh():
    """
    Recharge les actualités depuis brvm.org (usage admin / worker).
    Protéger en production (clé API ou réseau interne).
    """
    err = _require_news_admin()
    if err:
        return err

    from collectors.brvm_news_scraper import scrape_brvm_news

    try:
        payload = scrape_brvm_news(limit=int(request.args.get("limit", 20)))
        from storage.news_store import sync_scraped_articles

        synced = sync_scraped_articles(payload.get("articles") or [])
        invalidate_news_cache()
        return jsonify(
            {
                "ok": True,
                "articles_count": len(payload.get("articles") or []),
                "synced_to_database": synced,
                "generated_at": payload.get("generated_at"),
            }
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@news_bp.patch("/<slug>/status")
def news_set_status(slug):
    """Active ou désactive une actualité (admin)."""
    err = _require_news_admin()
    if err:
        return err

    payload = request.get_json(silent=True) or {}
    if "is_active" not in payload:
        return jsonify({"error": "Champ is_active requis."}), 400

    from storage.news_store import set_article_active

    try:
        article = set_article_active(slug, payload["is_active"])
        invalidate_news_cache()
        return jsonify({"article": serialize_article_detail(article)})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
