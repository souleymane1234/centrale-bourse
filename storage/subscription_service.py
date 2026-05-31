"""Essai 5 jours, abonnement mensuel, parrainage 20 %."""

import os
import secrets
from datetime import datetime, timedelta, timezone

from storage.models import ReferralEarning, Subscription, SubscriptionPlan, User, db

TRIAL_PLAN_CODE = "trial"
MONTHLY_PLAN_CODE = "pro_monthly"
TRIAL_DAYS = int(os.getenv("TRIAL_DURATION_DAYS", "5"))
REFERRAL_COMMISSION_RATE = float(os.getenv("REFERRAL_COMMISSION_RATE", "0.20"))
MONTHLY_DURATION_DAYS = 30


def _utcnow():
    return datetime.now(timezone.utc)


def _aware(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def generate_referral_code():
    for _ in range(20):
        code = secrets.token_hex(4).upper()
        if not User.query.filter_by(referral_code=code).first():
            return code
    return secrets.token_urlsafe(6).upper()[:12]


def ensure_user_referral_code(user):
    if user.referral_code:
        return user.referral_code
    user.referral_code = generate_referral_code()
    db.session.commit()
    return user.referral_code


def resolve_referrer(referral_code):
    code = (referral_code or "").strip().upper()
    if not code:
        return None
    return User.query.filter_by(referral_code=code, is_active=True).first()


def get_plan_by_code(code):
    return SubscriptionPlan.query.filter_by(code=code, is_active=True).first()


def expire_active_subscriptions(user):
    now = _utcnow()
    active = Subscription.query.filter_by(user_id=user.id, status="active").all()
    for sub in active:
        sub.status = "expired"
        sub.cancelled_at = now
        sub.updated_at = now


def create_subscription(user, plan, *, external_reference=None):
    now = _utcnow()
    expires = now + timedelta(days=int(plan.duration_days or MONTHLY_DURATION_DAYS))
    sub = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        status="active",
        started_at=now,
        expires_at=expires,
        auto_renew=False,
        external_reference=external_reference,
    )
    db.session.add(sub)
    return sub


def start_trial_subscription(user):
    plan = get_plan_by_code(TRIAL_PLAN_CODE) or get_plan_by_code("free")
    if not plan:
        return None
    expire_active_subscriptions(user)
    return create_subscription(user, plan)


def credit_referral_commission(referrer, referred_user, subscription, payment_fcfa, kind):
    if not referrer or referrer.id == referred_user.id:
        return None
    commission = int(round(payment_fcfa * REFERRAL_COMMISSION_RATE))
    if commission <= 0:
        return None

    referrer.referral_balance_fcfa = int(referrer.referral_balance_fcfa or 0) + commission
    earning = ReferralEarning(
        referrer_user_id=referrer.id,
        referred_user_id=referred_user.id,
        subscription_id=subscription.id if subscription else None,
        payment_fcfa=payment_fcfa,
        commission_fcfa=commission,
        commission_rate=REFERRAL_COMMISSION_RATE,
        kind=kind,
    )
    db.session.add(earning)
    return earning


def subscribe_monthly(user, *, payment_reference=None, mock_payment=None):
    plan = get_plan_by_code(MONTHLY_PLAN_CODE)
    if not plan:
        raise ValueError("Plan d'abonnement mensuel indisponible.")

    mock_ok = mock_payment if mock_payment is not None else os.getenv("PAYMENT_MOCK", "true").lower() == "true"
    if not mock_ok and not payment_reference:
        raise ValueError("Référence de paiement requise.")

    had_paid_before = (
        Subscription.query.join(SubscriptionPlan)
        .filter(
            Subscription.user_id == user.id,
            SubscriptionPlan.code == MONTHLY_PLAN_CODE,
            Subscription.status.in_(("active", "expired")),
        )
        .count()
        > 0
    )

    expire_active_subscriptions(user)
    subscription = create_subscription(
        user,
        plan,
        external_reference=payment_reference or f"mock-{secrets.token_hex(8)}",
    )

    referrer = user.referred_by if user.referred_by_user_id else None
    if referrer:
        kind = "renewal" if had_paid_before else "subscription"
        credit_referral_commission(
            referrer,
            user,
            subscription,
            plan.price_fcfa,
            kind,
        )

    db.session.commit()
    return subscription


def get_active_subscription(user):
    subs = (
        Subscription.query.filter_by(user_id=user.id, status="active")
        .order_by(Subscription.expires_at.desc())
        .all()
    )
    now = _utcnow()
    for sub in subs:
        expires = _aware(sub.expires_at)
        if expires and expires > now:
            return sub
        sub.status = "expired"
        sub.updated_at = now
    db.session.commit()
    return None


def subscription_days_remaining(subscription):
    if not subscription or not subscription.expires_at:
        return 0
    import math

    expires = _aware(subscription.expires_at)
    delta = (expires - _utcnow()).total_seconds()
    return max(0, int(math.ceil(delta / 86400))) if delta > 0 else 0


def user_access_state(user):
    sub = get_active_subscription(user)
    if not sub:
        return {
            "has_access": False,
            "reason": "expired",
            "days_remaining": 0,
            "is_trial": False,
            "is_paid": False,
            "can_subscribe": True,
        }

    plan_code = sub.plan.code if sub.plan else ""
    is_trial = plan_code in (TRIAL_PLAN_CODE, "free")
    is_paid = plan_code == MONTHLY_PLAN_CODE
    days = subscription_days_remaining(sub)

    return {
        "has_access": True,
        "reason": "trial" if is_trial else "subscription",
        "days_remaining": days,
        "is_trial": is_trial,
        "is_paid": is_paid,
        "can_subscribe": not is_paid,
    }


def referral_summary(user):
    ensure_user_referral_code(user)
    referred_count = User.query.filter_by(referred_by_user_id=user.id).count()
    earnings = (
        ReferralEarning.query.filter_by(referrer_user_id=user.id)
        .order_by(ReferralEarning.created_at.desc())
        .limit(50)
        .all()
    )
    total_commission = sum(item.commission_fcfa for item in earnings)
    return {
        "referral_code": user.referral_code,
        "balance_fcfa": int(user.referral_balance_fcfa or 0),
        "commission_rate_percent": int(REFERRAL_COMMISSION_RATE * 100),
        "referred_users_count": referred_count,
        "total_commission_fcfa": total_commission,
        "recent_earnings": [
            {
                "id": row.id,
                "commission_fcfa": row.commission_fcfa,
                "payment_fcfa": row.payment_fcfa,
                "kind": row.kind,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in earnings
        ],
    }
