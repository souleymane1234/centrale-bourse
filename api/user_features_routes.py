"""API : liste de suivi et alertes de cours."""

from flask import Blueprint, jsonify, request

from api.auth_routes import _require_user
from storage.user_features_service import (
    add_to_watchlist,
    create_price_alert,
    delete_price_alert,
    is_in_watchlist,
    list_price_alerts,
    list_watchlist,
    remove_from_watchlist,
    update_price_alert,
)

user_features_bp = Blueprint("user_features", __name__, url_prefix="/api/user")


@user_features_bp.get("/watchlist")
def get_watchlist():
    user, err = _require_user()
    if err:
        return err
    items = list_watchlist(user)
    return jsonify({"items": items, "count": len(items)})


@user_features_bp.get("/watchlist/<ticker>/status")
def watchlist_status(ticker):
    user, err = _require_user()
    if err:
        return err
    return jsonify({"ticker": ticker, "in_watchlist": is_in_watchlist(user, ticker)})


@user_features_bp.post("/watchlist")
def post_watchlist():
    user, err = _require_user()
    if err:
        return err
    payload = request.get_json(silent=True) or {}
    try:
        item = add_to_watchlist(user, payload.get("ticker"))
        return jsonify({"item": item}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@user_features_bp.delete("/watchlist/<ticker>")
def delete_watchlist(ticker):
    user, err = _require_user()
    if err:
        return err
    try:
        return jsonify(remove_from_watchlist(user, ticker))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@user_features_bp.get("/alerts")
def get_alerts():
    user, err = _require_user()
    if err:
        return err
    alerts = list_price_alerts(user)
    triggered = sum(1 for alert in alerts if alert.get("is_triggered"))
    return jsonify(
        {
            "alerts": alerts,
            "count": len(alerts),
            "triggered_count": triggered,
            "notifications_note": "Les notifications par email et SMS seront disponibles prochainement.",
        }
    )


@user_features_bp.post("/alerts")
def post_alert():
    user, err = _require_user()
    if err:
        return err
    payload = request.get_json(silent=True) or {}
    try:
        alert = create_price_alert(
            user,
            ticker=payload.get("ticker"),
            direction=payload.get("direction"),
            target_price=payload.get("target_price"),
            note=payload.get("note"),
        )
        return jsonify({"alert": alert}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@user_features_bp.patch("/alerts/<int:alert_id>")
def patch_alert(alert_id):
    user, err = _require_user()
    if err:
        return err
    payload = request.get_json(silent=True) or {}
    try:
        alert = update_price_alert(
            user,
            alert_id,
            is_active=payload.get("is_active"),
            target_price=payload.get("target_price"),
            note=payload.get("note"),
        )
        return jsonify({"alert": alert})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@user_features_bp.delete("/alerts/<int:alert_id>")
def delete_alert(alert_id):
    user, err = _require_user()
    if err:
        return err
    try:
        return jsonify(delete_price_alert(user, alert_id))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
