"""
Actionnariat : priorité aux « Principaux actionnaires » Sikafinance.
"""


def build_shareholding_payload(company):
    """Retourne l'actionnariat à afficher (Sikafinance en priorité)."""
    if not company:
        return {"shareholders": [], "total_shares": None, "source": None}

    profile = company.get("sikafinance_profile") or {}
    sikafinance_shareholders = profile.get("shareholders") or []

    if sikafinance_shareholders:
        market_stats = profile.get("market_stats") or {}
        total_shares = market_stats.get("shares_outstanding")
        return {
            "source": "sikafinance",
            "source_label": "Principaux actionnaires",
            "shareholders": sikafinance_shareholders,
            "total_shares": total_shares,
        }

    brvm = company.get("shareholding") or {}
    brvm_shareholders = brvm.get("shareholders") or []
    if brvm_shareholders:
        total = brvm.get("total_shares")
        total_value = total.get("value") if isinstance(total, dict) else total
        return {
            "source": "brvm",
            "source_label": "Actionnariat BRVM",
            "shareholders": brvm_shareholders,
            "total_shares": total_value,
            "total_shares_as_of": total.get("as_of") if isinstance(total, dict) else None,
        }

    return {"shareholders": [], "total_shares": None, "source": None}
