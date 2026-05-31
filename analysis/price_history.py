"""Résolution de l'historique de cours pour les graphiques."""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def compute_previous_close(quote):
    """Déduit le cours de clôture précédent à partir du dernier cours et de la variation (%)."""
    if not quote:
        return None

    last = quote.get("last")
    variation = quote.get("variation_pct")
    if last is not None and variation is not None:
        previous = float(last) / (1 + float(variation) / 100)
        rounded = round(previous)
        if abs(previous - rounded) < 0.25:
            return float(rounded)
        return round(previous, 2)

    opening = quote.get("opening")
    if opening is not None and last is not None and float(opening) != float(last):
        return round(float(opening), 2)

    return round(float(last), 2) if last is not None else None


def _business_days(count, end_date=None):
    end = end_date or datetime.now().date()
    days = []
    cursor = end
    while len(days) < count:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor -= timedelta(days=1)
    days.reverse()
    return days


def build_price_history_from_quote(market_quote, ticker=None, days=60):
    """Historique estimé à partir de la seule cotation du jour (secours)."""
    if not market_quote or market_quote.get("last") is None:
        return pd.DataFrame(), None

    last = float(market_quote["last"])
    opening = float(market_quote.get("opening") or last)
    high = float(market_quote.get("high") or max(opening, last))
    low = float(market_quote.get("low") or min(opening, last))
    volume = market_quote.get("volume_shares")
    prev_close = compute_previous_close(market_quote) or opening

    dates = _business_days(days)
    session_count = len(dates)
    if session_count < 2:
        return pd.DataFrame(), None

    seed = abs(hash(str(ticker or market_quote.get("code") or last))) % (2**32)
    rng = np.random.default_rng(seed)

    interior_count = session_count - 2
    if interior_count > 0:
        start_price = prev_close * 0.92
        path = np.linspace(start_price, prev_close, interior_count + 1)
        noise = rng.normal(0, 0.004, size=interior_count + 1)
        path = path * (1 + noise)
        path[0] = start_price
        path[-1] = prev_close
        closes = list(path) + [prev_close, last]
    else:
        closes = [prev_close, last]

    closes = closes[-session_count:]
    closes[-2] = prev_close
    closes[-1] = last

    rows = []
    for index, day in enumerate(dates):
        is_today = index == session_count - 1
        is_yesterday = index == session_count - 2

        if is_today:
            row_open, row_high, row_low, row_close = opening, high, low, last
            row_volume = volume or 0
        elif is_yesterday:
            row_open = row_high = row_low = row_close = prev_close
            row_volume = 0
        else:
            row_close = float(closes[index])
            prev_row_close = float(closes[index - 1]) if index > 0 else row_close
            row_open = prev_row_close
            wiggle = abs(rng.normal(0, 0.003))
            row_high = round(max(row_open, row_close) * (1 + wiggle), 2)
            row_low = round(min(row_open, row_close) * (1 - wiggle), 2)
            row_volume = 0

        rows.append(
            {
                "date": day.strftime("%Y-%m-%d"),
                "open": round(float(row_open), 2),
                "high": round(float(row_high), 2),
                "low": round(float(row_low), 2),
                "close": round(float(row_close), 2),
                "volume": int(row_volume) if row_volume else 0,
            }
        )

    meta = {
        "source": "estimated",
        "sessions": session_count,
        "previous_close": prev_close,
        "last": last,
    }
    return pd.DataFrame(rows), meta


def load_price_history_from_database(db, ticker, days=120, min_sessions=10):
    """Charge l'historique stocké en base."""
    if not db or not ticker:
        return pd.DataFrame(), None

    stored = db.get_stock_prices(ticker, days=days)
    if stored.empty or len(stored) < min_sessions:
        return pd.DataFrame(), None

    first_date, last_date = db.get_price_date_range(ticker)
    source_label = "sikafinance_historique"
    if "source" in stored.columns and not stored["source"].empty:
        source_label = str(stored["source"].iloc[-1])

    meta = {
        "source": "database",
        "data_origin": source_label,
        "sessions": len(stored),
        "first_date": first_date,
        "last_date": last_date,
    }
    return stored, meta


def resolve_price_history(
    company, ticker, days=120, legacy_fetch=None, db=None, ensure_history=True
):
    """
    Priorité : base MySQL (historique réel) > estimation > collecteur legacy.
    """
    if ensure_history and db and ticker and company:
        try:
            from storage.price_sync import ensure_company_price_history

            ensure_company_price_history(company, db=db)
        except Exception as exc:
            print(f"⚠️  Historique {ticker} : {exc}")

    if db and ticker:
        stored_df, meta = load_price_history_from_database(db, ticker, days=days)
        if not stored_df.empty:
            return stored_df, meta

    market_quote = (company or {}).get("market_quote") or {}
    df, meta = build_price_history_from_quote(market_quote, ticker=ticker, days=days)
    if not df.empty:
        return df, meta

    if legacy_fetch:
        legacy_df = legacy_fetch()
        if legacy_df is not None and not legacy_df.empty:
            return legacy_df, {
                "source": "legacy",
                "sessions": len(legacy_df),
                "note": "Historique issu du collecteur de secours.",
            }

    return pd.DataFrame(), {"source": "none", "sessions": 0, "note": "Aucun historique disponible."}
