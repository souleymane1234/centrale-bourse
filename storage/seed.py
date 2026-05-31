"""Données initiales (plans d'abonnement)."""

from storage.models import SubscriptionPlan, db

DEFAULT_PLANS = [
    {
        "code": "trial",
        "name": "Essai offert",
        "description": "Accès complet à la plateforme pendant 5 jours (cadeau à l'inscription).",
        "price_fcfa": 0,
        "billing_period": "trial",
        "duration_days": 5,
        "features": {
            "full_platform": True,
            "trial_days": 5,
        },
    },
    {
        "code": "free",
        "name": "Gratuit (legacy)",
        "description": "Ancien plan — remplacé par l'essai 5 jours.",
        "price_fcfa": 0,
        "billing_period": "trial",
        "duration_days": 5,
        "features": {"full_platform": True},
        "is_active": False,
    },
    {
        "code": "pro_monthly",
        "name": "Abonnement mensuel",
        "description": "Accès complet pendant 1 mois, renouvelable.",
        "price_fcfa": 2500,
        "billing_period": "monthly",
        "duration_days": 30,
        "features": {
            "full_platform": True,
            "max_watchlist": 50,
            "alerts": True,
            "advanced_charts": True,
        },
    },
]


def seed_subscription_plans():
    created = 0
    for plan_data in DEFAULT_PLANS:
        existing = SubscriptionPlan.query.filter_by(code=plan_data["code"]).first()
        if existing:
            for key in ("name", "description", "price_fcfa", "duration_days", "billing_period", "features"):
                if key in plan_data:
                    setattr(existing, key, plan_data[key])
            if "is_active" in plan_data:
                existing.is_active = plan_data["is_active"]
            continue
        payload = {**plan_data}
        is_active = payload.pop("is_active", True)
        db.session.add(SubscriptionPlan(**payload, is_active=is_active))
        created += 1
    db.session.commit()
    return created
