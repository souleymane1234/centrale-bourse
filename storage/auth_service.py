"""Authentification utilisateurs et sessions."""

import secrets
from datetime import datetime, timedelta, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from storage.models import Subscription, User, UserSession, db
from storage.subscription_service import (
    ensure_user_referral_code,
    get_active_subscription,
    payments_enabled,
    referral_summary,
    resolve_referrer,
    start_trial_subscription,
    subscription_days_remaining,
    user_access_state,
)


def create_user(email, password, full_name=None, phone=None, referral_code=None):
    email = (email or "").strip().lower()
    if not email or not password:
        raise ValueError("Email et mot de passe requis.")
    if len(password) < 8:
        raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
    if User.query.filter_by(email=email).first():
        raise ValueError("Un compte existe déjà avec cet email.")

    referrer = resolve_referrer(referral_code)

    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        full_name=(full_name or "").strip() or None,
        phone=(phone or "").strip() or None,
        role="user",
        referred_by_user_id=referrer.id if referrer else None,
        referral_code=secrets.token_hex(4).upper(),
    )
    db.session.add(user)
    db.session.flush()

    ensure_user_referral_code(user)
    start_trial_subscription(user)
    db.session.commit()
    return user


def authenticate_user(email, password):
    email = (email or "").strip().lower()
    user = User.query.filter_by(email=email, is_active=True).first()
    if not user or not check_password_hash(user.password_hash, password):
        return None, None

    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=int(30))
    session = UserSession(user_id=user.id, token=token, expires_at=expires)
    db.session.add(session)
    db.session.commit()
    return user, session


def logout_user(token):
    if not token:
        return
    session = UserSession.query.filter_by(token=token).first()
    if session:
        db.session.delete(session)
        db.session.commit()


def get_user_by_token(token):
    if not token:
        return None
    session = UserSession.query.filter_by(token=token).first()
    if not session:
        return None
    expires = session.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        db.session.delete(session)
        db.session.commit()
        return None
    return session.user


def update_user_profile(user, *, full_name=None, phone=None, password=None):
    if full_name is not None:
        user.full_name = (full_name or "").strip() or None
    if phone is not None:
        user.phone = (phone or "").strip() or None
    if password:
        if len(password) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
        user.password_hash = generate_password_hash(password)
    user.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return user


def serialize_user(user):
    active_sub = get_active_subscription(user)
    plan = active_sub.plan if active_sub else None
    access = user_access_state(user)
    referral = referral_summary(user)

    return {
        "id": user.id,
        "payments_enabled": payments_enabled(),
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "referral_code": referral["referral_code"],
        "referral_balance_fcfa": referral["balance_fcfa"],
        "referred_by_user_id": user.referred_by_user_id,
        "access": access,
        "subscription": {
            "status": active_sub.status if active_sub else None,
            "started_at": active_sub.started_at.isoformat() if active_sub and active_sub.started_at else None,
            "expires_at": active_sub.expires_at.isoformat() if active_sub and active_sub.expires_at else None,
            "days_remaining": subscription_days_remaining(active_sub) if active_sub else 0,
            "is_trial": access["is_trial"],
            "is_paid": access["is_paid"],
            "plan": {
                "code": plan.code,
                "name": plan.name,
                "price_fcfa": plan.price_fcfa,
                "duration_days": plan.duration_days,
                "billing_period": plan.billing_period,
            }
            if plan
            else None,
        },
        "referral": referral,
    }
