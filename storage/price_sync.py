"""Synchronisation des cotations Sikafinance vers la base de données."""

import json
import os
import time
from datetime import datetime

from collectors.company_info_scraper import CompanyInfoScraper
from storage.database import create_database
from storage.tickers import derive_company_ticker, normalize_identifier

MIN_HISTORY_SESSIONS = int(os.getenv("MIN_HISTORY_SESSIONS", "20"))
HISTORY_FETCH_MAX_ROWS = int(os.getenv("HISTORY_FETCH_MAX_ROWS", "365"))
HISTORY_FETCH_DELAY_SECONDS = float(os.getenv("HISTORY_FETCH_DELAY_SECONDS", "0.4"))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPANIES_JSON = os.path.join(BASE_DIR, "data", "companies_full.json")


def _build_enriched_lookup(companies):
    """Index des fiches JSON pour enrichir les cotations live."""
    lookup = {}

    for company in companies:
        record = dict(company)
        ticker = derive_company_ticker(record)
        if ticker:
            lookup[ticker] = record

        quote = record.get("market_quote") or {}
        code = quote.get("code")
        if code:
            symbol_key = normalize_identifier(code.split(".", 1)[0])
            if symbol_key:
                lookup[symbol_key] = record

        for field in [
            record.get("display_name"),
            record.get("profile_name"),
            record.get("legal_name"),
            (record.get("brvm_reports_reference") or {}).get("issuer"),
            quote.get("name"),
        ]:
            key = normalize_identifier(field)
            if key:
                lookup[key] = record

    return lookup


def sync_quotes_from_company_records(companies, db=None, trade_date=None):
    """
    Enregistre les cotations du jour pour chaque société listée.
    Retourne le nombre de cours synchronisés.
    """
    database = db or create_database()
    trade_date = trade_date or datetime.now().strftime("%Y-%m-%d")
    return database.sync_companies_quotes(companies, trade_date=trade_date)


def sync_live_sikafinance_listing(db=None, companies_from_json=None, trade_date=None):
    """
    Synchronise la liste officielle Sikafinance (48 cotations) vers MySQL.
    Enrichit avec companies_full.json quand une fiche existe.
    Retourne (cours_synced, companies_count).
    """
    database = db or create_database()
    trade_date = trade_date or datetime.now().strftime("%Y-%m-%d")
    companies_from_json = companies_from_json or []

    lookup = _build_enriched_lookup(companies_from_json)
    quotes = CompanyInfoScraper().fetch_sikafinance_market_data().get("quotes", [])

    records = []
    seen_codes = set()

    for quote in quotes:
        code = quote.get("code")
        if not code or code in seen_codes:
            continue
        seen_codes.add(code)

        symbol = code.split(".", 1)[0]
        match_keys = [
            normalize_identifier(symbol),
            normalize_identifier(code),
            normalize_identifier(quote.get("name")),
        ]

        base = None
        for key in match_keys:
            if key and key in lookup:
                base = dict(lookup[key])
                break

        if base is None:
            base = {
                "display_name": quote.get("name"),
                "symbol": symbol,
            }

        base["market_quote"] = quote
        if not base.get("symbol"):
            base["symbol"] = symbol
        base["ticker"] = derive_company_ticker(base) or normalize_identifier(symbol)
        records.append(base)

    synced = sync_quotes_from_company_records(records, db=database, trade_date=trade_date)
    return synced, len(records)


def sync_quotes_from_market_payload(quotes, lookup_by_code=None, db=None, trade_date=None):
    """Enregistre des cotations à partir d'une liste brute Sikafinance."""
    database = db or create_database()
    trade_date = trade_date or datetime.now().strftime("%Y-%m-%d")
    lookup_by_code = lookup_by_code or {}
    synced = 0

    for quote in quotes:
        code = quote.get("code")
        company = lookup_by_code.get(code) if code else None
        if not company:
            continue
        record = dict(company)
        record["market_quote"] = quote
        if database.sync_company_quote(record, trade_date=trade_date):
            synced += 1

    return synced


def backfill_from_companies_payload(payload, db=None):
    """
    Import complet : cotations live Sikafinance (48) + indices du JSON.
    Le JSON seul ne contient souvent que ~44 cours (dernier scrape).
    """
    database = db or create_database()
    companies = payload.get("companies", [])

    synced, listed_count = sync_live_sikafinance_listing(
        db=database,
        companies_from_json=companies,
    )

    if hasattr(database, "sync_market_indices"):
        database.sync_market_indices(payload.get("market_indices", []))

    return synced, listed_count


def _sikafinance_code_for_company(company):
    quote = company.get("market_quote") or {}
    return quote.get("code") or company.get("sikafinance_code")


def sync_company_price_history(company, db=None, max_rows=None):
    """
    Récupère l'historique OHLCV Sikafinance et l'enregistre en base.
    Retourne le nombre de séances importées.
    """
    ticker = company.get("ticker")
    code = _sikafinance_code_for_company(company)
    if not ticker or not code:
        return 0

    database = db or create_database()
    if not hasattr(database, "bulk_upsert_stock_prices"):
        return 0

    scraper = CompanyInfoScraper()
    rows = scraper.fetch_sikafinance_price_history(
        code,
        max_rows=max_rows or HISTORY_FETCH_MAX_ROWS,
    )
    if not rows:
        return 0

    database.upsert_company(company)
    saved = database.bulk_upsert_stock_prices(
        ticker,
        rows,
        source="sikafinance_historique",
    )
    return saved


def ensure_company_price_history(company, db=None, min_sessions=None):
    """
    Complète l'historique en base si trop peu de séances (graphiques réels).
    """
    ticker = company.get("ticker")
    if not ticker:
        return 0

    database = db or create_database()
    threshold = min_sessions if min_sessions is not None else MIN_HISTORY_SESSIONS
    current = database.count_stock_prices(ticker)
    if current >= threshold:
        return current

    imported = sync_company_price_history(company, db=database)
    return database.count_stock_prices(ticker) if imported else current


def backfill_all_price_histories(companies, db=None, delay_seconds=None):
    """Importe l'historique Sikafinance pour toutes les sociétés listées."""
    database = db or create_database()
    delay = HISTORY_FETCH_DELAY_SECONDS if delay_seconds is None else delay_seconds
    total_sessions = 0
    success = 0

    for index, company in enumerate(companies):
        ticker = company.get("ticker")
        if not ticker:
            continue
        try:
            imported = sync_company_price_history(company, db=database)
            if imported:
                success += 1
                total_sessions += imported
                print(f"  📈 {ticker}: {imported} séances")
        except Exception as exc:
            print(f"  ⚠️  {ticker}: {exc}")
        if delay and index < len(companies) - 1:
            time.sleep(delay)

    return success, total_sessions


def backfill_from_json_file(db=None, json_path=None):
    """Charge companies_full.json puis synchronise via Sikafinance live."""
    json_path = json_path or COMPANIES_JSON
    if not os.path.exists(json_path):
        raise FileNotFoundError(json_path)

    with open(json_path, "r", encoding="utf-8") as file:
        payload = json.load(file)

    return backfill_from_companies_payload(payload, db=db)
