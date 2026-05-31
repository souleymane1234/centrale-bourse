"""Identifiants sociétés (tickers) partagés API / base de données."""

import re


def normalize_identifier(value):
    if not value:
        return None
    normalized = re.sub(r"[^A-Z0-9]+", "", str(value).upper())
    return normalized or None


def derive_company_ticker(company):
    """
    Ticker stable pour URLs, base SQLite et API.
    Priorité : symbole BRVM > code Sikafinance > émetteur > nom.
    """
    if not company:
        return None

    symbol = company.get("symbol")
    normalized = normalize_identifier(symbol)
    if normalized and len(normalized) <= 8:
        return normalized

    quote = company.get("market_quote") or {}
    code = quote.get("code")
    if code:
        code_symbol = code.split(".", 1)[0]
        normalized = normalize_identifier(code_symbol)
        if normalized:
            return normalized

    candidates = [
        company.get("ticker"),
        (company.get("brvm_reports_reference") or {}).get("issuer"),
        quote.get("name"),
        company.get("profile_name"),
        company.get("display_name"),
    ]

    for candidate in candidates:
        normalized = normalize_identifier(candidate)
        if normalized:
            return normalized

    return None
