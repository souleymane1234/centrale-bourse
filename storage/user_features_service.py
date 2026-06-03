"""Liste de suivi (watchlist) et alertes de cours."""

import os

from storage.models import User, UserPriceAlert, UserWatchlistItem, db
from storage.tickers import normalize_identifier

MAX_WATCHLIST_ITEMS = int(os.getenv("MAX_WATCHLIST_ITEMS", "50"))
MAX_PRICE_ALERTS = int(os.getenv("MAX_PRICE_ALERTS", "20"))


def _normalize_ticker(ticker):
    normalized = normalize_identifier(ticker)
    if not normalized:
        raise ValueError("Ticker invalide.")
    return normalized


def _quote_snapshot(ticker):
    try:
        from app import get_company_by_ticker, serialize_company_for_selector

        company = get_company_by_ticker(ticker)
        if not company:
            return None
        row = serialize_company_for_selector(company)
        return {
            "ticker": row["ticker"],
            "name": row["name"],
            "symbol": row["symbol"],
            "sector": row["sector"],
            "price": row["price"],
            "variation": row["variation"],
            "code": row.get("code"),
        }
    except Exception:
        return {"ticker": ticker, "name": ticker, "symbol": ticker}


def _alert_triggered(alert, current_price):
    if current_price is None or not alert.is_active:
        return False
    price = float(current_price)
    target = float(alert.target_price)
    if alert.direction == "above":
        return price >= target
    return price <= target


def serialize_watchlist_item(item):
    snapshot = _quote_snapshot(item.ticker)
    return {
        "id": item.id,
        "ticker": item.ticker,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "company": snapshot,
    }


def serialize_price_alert(alert):
    snapshot = _quote_snapshot(alert.ticker)
    current_price = (snapshot or {}).get("price")
    triggered = _alert_triggered(alert, current_price)
    return {
        "id": alert.id,
        "ticker": alert.ticker,
        "direction": alert.direction,
        "target_price": alert.target_price,
        "is_active": alert.is_active,
        "note": alert.note,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
        "company": snapshot,
        "current_price": current_price,
        "is_triggered": triggered,
        "notifications_enabled": False,
    }


def list_watchlist(user):
    items = (
        UserWatchlistItem.query.filter_by(user_id=user.id)
        .order_by(UserWatchlistItem.created_at.desc())
        .all()
    )
    return [serialize_watchlist_item(item) for item in items]


def add_to_watchlist(user, ticker):
    normalized = _normalize_ticker(ticker)
    existing = UserWatchlistItem.query.filter_by(user_id=user.id, ticker=normalized).first()
    if existing:
        return serialize_watchlist_item(existing)

    count = UserWatchlistItem.query.filter_by(user_id=user.id).count()
    if count >= MAX_WATCHLIST_ITEMS:
        raise ValueError(f"Limite de {MAX_WATCHLIST_ITEMS} sociétés en liste de suivi.")

    item = UserWatchlistItem(user_id=user.id, ticker=normalized)
    db.session.add(item)
    db.session.commit()
    return serialize_watchlist_item(item)


def remove_from_watchlist(user, ticker):
    normalized = _normalize_ticker(ticker)
    item = UserWatchlistItem.query.filter_by(user_id=user.id, ticker=normalized).first()
    if not item:
        raise ValueError("Cette société n'est pas dans votre liste de suivi.")
    db.session.delete(item)
    db.session.commit()
    return {"ok": True, "ticker": normalized}


def is_in_watchlist(user, ticker):
    if not user:
        return False
    normalized = _normalize_ticker(ticker)
    return (
        UserWatchlistItem.query.filter_by(user_id=user.id, ticker=normalized).first()
        is not None
    )


def list_price_alerts(user):
    alerts = (
        UserPriceAlert.query.filter_by(user_id=user.id)
        .order_by(UserPriceAlert.created_at.desc())
        .all()
    )
    return [serialize_price_alert(alert) for alert in alerts]


def create_price_alert(user, *, ticker, direction, target_price, note=None):
    normalized = _normalize_ticker(ticker)
    direction = (direction or "").strip().lower()
    if direction not in ("above", "below"):
        raise ValueError("Direction invalide (above ou below).")

    try:
        target = float(target_price)
    except (TypeError, ValueError) as exc:
        raise ValueError("Prix cible invalide.") from exc
    if target <= 0:
        raise ValueError("Le prix cible doit être strictement positif.")

    active_count = UserPriceAlert.query.filter_by(user_id=user.id, is_active=True).count()
    if active_count >= MAX_PRICE_ALERTS:
        raise ValueError(f"Limite de {MAX_PRICE_ALERTS} alertes actives.")

    alert = UserPriceAlert(
        user_id=user.id,
        ticker=normalized,
        direction=direction,
        target_price=target,
        note=(note or "").strip() or None,
        is_active=True,
    )
    db.session.add(alert)
    db.session.commit()
    return serialize_price_alert(alert)


def update_price_alert(user, alert_id, *, is_active=None, target_price=None, note=None):
    alert = UserPriceAlert.query.filter_by(id=alert_id, user_id=user.id).first()
    if not alert:
        raise ValueError("Alerte introuvable.")

    if is_active is not None:
        alert.is_active = bool(is_active)
        if alert.is_active:
            active_count = UserPriceAlert.query.filter(
                UserPriceAlert.user_id == user.id,
                UserPriceAlert.is_active.is_(True),
                UserPriceAlert.id != alert.id,
            ).count()
            if active_count >= MAX_PRICE_ALERTS:
                raise ValueError(f"Limite de {MAX_PRICE_ALERTS} alertes actives.")

    if target_price is not None:
        try:
            target = float(target_price)
        except (TypeError, ValueError) as exc:
            raise ValueError("Prix cible invalide.") from exc
        if target <= 0:
            raise ValueError("Le prix cible doit être strictement positif.")
        alert.target_price = target

    if note is not None:
        alert.note = (note or "").strip() or None

    db.session.commit()
    return serialize_price_alert(alert)


def delete_price_alert(user, alert_id):
    alert = UserPriceAlert.query.filter_by(id=alert_id, user_id=user.id).first()
    if not alert:
        raise ValueError("Alerte introuvable.")
    db.session.delete(alert)
    db.session.commit()
    return {"ok": True, "id": alert_id}
