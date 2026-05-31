"""
Construction des indicateurs financiers (Sikafinance prioritaire, repli BRVM).
"""
import re


def _normalize_label(value):
    if not value:
        return ""
    text = str(value).lower()
    text = text.replace("'", "'").replace("é", "e").replace("è", "e")
    return re.sub(r"\s+", " ", text).strip()


def _compute_growth_pct(current, previous):
    if current is None or previous is None:
        return None
    try:
        prev = float(previous)
        cur = float(current)
    except (TypeError, ValueError):
        return None
    if prev == 0:
        return None
    return round((cur - prev) / abs(prev) * 100, 2)


def _enrich_brvm_history(rows):
    """Complète l'historique BRVM (CA, RN, dividende) avec croissances calculées."""
    if not rows:
        return []

    ordered = sorted(rows, key=lambda item: item.get("year") or 0)
    enriched = []
    for index, row in enumerate(ordered):
        entry = dict(row)
        prev = ordered[index - 1] if index > 0 else None
        if entry.get("revenue_growth_pct") is None and prev:
            entry["revenue_growth_pct"] = _compute_growth_pct(
                entry.get("revenue_mfcfa"), prev.get("revenue_mfcfa")
            )
        if entry.get("net_income_growth_pct") is None and prev:
            entry["net_income_growth_pct"] = _compute_growth_pct(
                entry.get("net_income_mfcfa"), prev.get("net_income_mfcfa")
            )
        entry.setdefault("eps_fcfa", None)
        entry.setdefault("pe_ratio", None)
        entry.setdefault(
            "dividend_per_share_fcfa",
            entry.pop("net_dividend_per_share_fcfa", None),
        )
        enriched.append(entry)
    return enriched


def get_financial_statements(company):
    """Retourne jusqu'à 5 exercices, du plus récent au plus ancien pour l'affichage."""
    if not company:
        return []

    profile = company.get("sikafinance_profile") or {}
    sikafinance_rows = profile.get("financial_statements") or []
    if sikafinance_rows:
        ordered = sorted(sikafinance_rows, key=lambda item: item.get("year") or 0, reverse=True)
        return ordered[:5]

    brvm_rows = company.get("financial_history") or []
    if brvm_rows:
        ordered = sorted(
            _enrich_brvm_history(brvm_rows),
            key=lambda item: item.get("year") or 0,
            reverse=True,
        )
        return ordered[:5]

    return []


def get_market_stats(company):
    """Statistiques de marché Sikafinance (titres, flottant, valorisation)."""
    if not company:
        return None

    profile = company.get("sikafinance_profile") or {}
    stats = profile.get("market_stats") or company.get("market_stats")
    if not stats:
        return None

    return {
        "shares_outstanding": stats.get("shares_outstanding"),
        "float_pct": stats.get("float_pct"),
        "market_cap_mfcfa": stats.get("market_cap_mfcfa"),
        "market_cap_raw": stats.get("market_cap_raw"),
    }


def build_financial_payload(company):
    statements = get_financial_statements(company)
    chart_rows = sorted(statements, key=lambda item: item.get("year") or 0)
    return {
        "market_stats": get_market_stats(company),
        "statements": statements,
        "chart": {
            "revenue": [
                {"year": row.get("year"), "value_mfcfa": row.get("revenue_mfcfa")}
                for row in chart_rows
                if row.get("revenue_mfcfa") is not None
            ],
            "net_income": [
                {"year": row.get("year"), "value_mfcfa": row.get("net_income_mfcfa")}
                for row in chart_rows
                if row.get("net_income_mfcfa") is not None
            ],
        },
        "source": "sikafinance"
        if (company or {}).get("sikafinance_profile", {}).get("financial_statements")
        else ("brvm" if (company or {}).get("financial_history") else None),
    }
