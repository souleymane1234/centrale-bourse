"""Routes API : utilisateurs, abonnements et parrainage."""

from flask import Blueprint, jsonify, request

from storage.auth_service import (
    authenticate_user,
    create_user,
    get_user_by_token,
    logout_user,
    serialize_user,
    update_user_profile,
)
from storage.models import SubscriptionPlan, db
from storage.subscription_service import payments_enabled, referral_summary, subscribe_monthly

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
subscriptions_bp = Blueprint("subscriptions", __name__, url_prefix="/api/subscriptions")
referrals_bp = Blueprint("referrals", __name__, url_prefix="/api/referrals")


def _bearer_token():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:].strip()
    return request.headers.get("X-Auth-Token")


def _require_user():
    user = get_user_by_token(_bearer_token())
    if not user:
        return None, (jsonify({"error": "Non authentifié."}), 401)
    return user, None


@auth_bp.get("/config")
def public_config():
    return jsonify({"payments_enabled": payments_enabled()})


@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    try:
        user = create_user(
            email=payload.get("email"),
            password=payload.get("password"),
            full_name=payload.get("full_name"),
            phone=payload.get("phone"),
            referral_code=payload.get("referral_code"),
        )
        _, session = authenticate_user(payload.get("email"), payload.get("password"))
        return jsonify(
            {
                "token": session.token,
                "expires_at": session.expires_at.isoformat(),
                "user": serialize_user(user),
            }
        ), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    user, session = authenticate_user(payload.get("email"), payload.get("password"))
    if not user:
        return jsonify({"error": "Identifiants invalides."}), 401
    return jsonify(
        {
            "token": session.token,
            "expires_at": session.expires_at.isoformat(),
            "user": serialize_user(user),
        }
    )


@auth_bp.post("/logout")
def logout():
    logout_user(_bearer_token())
    return jsonify({"ok": True})


@auth_bp.get("/me")
def me():
    user, err = _require_user()
    if err:
        return err
    return jsonify({"user": serialize_user(user)})


@auth_bp.patch("/me")
def update_me():
    user, err = _require_user()
    if err:
        return err
    payload = request.get_json(silent=True) or {}
    try:
        update_user_profile(
            user,
            full_name=payload.get("full_name"),
            phone=payload.get("phone"),
            password=payload.get("password"),
        )
        return jsonify({"user": serialize_user(user)})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@subscriptions_bp.get("/plans")
def list_plans():
    if not payments_enabled():
        return jsonify({"plans": []})
    plans = (
        SubscriptionPlan.query.filter_by(is_active=True)
        .filter(SubscriptionPlan.code == "pro_monthly")
        .order_by(SubscriptionPlan.price_fcfa.asc())
        .all()
    )
    return jsonify(
        {
            "plans": [
                {
                    "id": plan.id,
                    "code": plan.code,
                    "name": plan.name,
                    "description": plan.description,
                    "price_fcfa": plan.price_fcfa,
                    "billing_period": plan.billing_period,
                    "duration_days": plan.duration_days,
                    "features": plan.features or {},
                }
                for plan in plans
            ]
        }
    )


@subscriptions_bp.get("/me")
def my_subscription():
    user, err = _require_user()
    if err:
        return err
    return jsonify({"user": serialize_user(user)})


@subscriptions_bp.post("/subscribe")
def subscribe():
    if not payments_enabled():
        return jsonify({"error": "Les paiements ne sont pas activés pour le moment."}), 503
    user, err = _require_user()
    if err:
        return err
    payload = request.get_json(silent=True) or {}
    plan_code = (payload.get("plan_code") or "pro_monthly").strip()
    if plan_code != "pro_monthly":
        return jsonify({"error": "Seul l'abonnement mensuel est disponible."}), 400
    try:
        subscribe_monthly(
            user,
            payment_reference=payload.get("payment_reference"),
            mock_payment=payload.get("mock_payment"),
        )
        return jsonify({"user": serialize_user(user), "message": "Abonnement activé pour 30 jours."})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@referrals_bp.get("/me")
def my_referrals():
    user, err = _require_user()
    if err:
        return err
    return jsonify(referral_summary(user))
