from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from collectors.brvm_scraper import BRVMRealScraper
from collectors.brvm_collector import BRVMCollector
from analysis.technical import TechnicalAnalysis
from analysis.fundamental import FundamentalAnalysis
from analysis.price_history import compute_previous_close, resolve_price_history
from storage.app_factory import configure_app
from storage.config import get_db_engine
from storage.database import create_database
from storage.models import SubscriptionPlan, User, db as sa_db
from storage.price_sync import sync_quotes_from_company_records
from storage.seed import seed_subscription_plans
from api.auth_routes import auth_bp, referrals_bp, subscriptions_bp
from api.news_routes import news_bp
from storage.tickers import derive_company_ticker as storage_derive_company_ticker
from storage.tickers import normalize_identifier as storage_normalize_identifier
from collectors.company_info_scraper import CompanyInfoScraper
import json
import pandas as pd
import os
from datetime import datetime, timezone
import re
import time
import unicodedata

from jobs.company_data_refresh import get_scrape_status, start_scrape_scheduler
from jobs.palmares_refresh import get_palmares_refresh_status, start_palmares_scheduler
from storage.palmares_store import load_palmares_snapshot, save_palmares_snapshot
from storage.cache_service import (
    cache_delete,
    cache_status,
    get_or_build,
    invalidate_keys,
    invalidate_pattern,
)
from api.rate_limit import check_request_limit

CACHE_KEY_LISTED = 'listed_companies'
CACHE_KEY_COMPARE = 'compare_dashboard'
CACHE_KEY_PALMARES = 'palmares'
CACHE_KEY_MARKET_SUMMARY = 'market_summary'
CACHE_KEY_HOME = 'home'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.join(BASE_DIR, 'static', 'frontend')

app = Flask(__name__, static_folder=None)
configure_app(app)

CORS(
    app,
    resources={r'/api/*': {'origins': os.getenv('CORS_ORIGINS', '*').split(',')}},
)

app.register_blueprint(auth_bp)
app.register_blueprint(subscriptions_bp)
app.register_blueprint(referrals_bp)
app.register_blueprint(news_bp)

def init_database_schema():
    """Crée les tables MySQL/SQLite au démarrage."""
    if os.getenv('DB_AUTO_CREATE', 'true').lower() in ('0', 'false', 'no'):
        return
    try:
        sa_db.create_all()
        seed_subscription_plans()
        print(f"✅ Base initialisée ({get_db_engine()}) — tables prêtes.")
    except Exception as exc:
        print(f"❌ Impossible de créer les tables : {exc}")
        print("   → Lancez : python scripts/init_database.py")


with app.app_context():
    init_database_schema()

# Initialisation des composants
scraper = BRVMRealScraper()
collector = BRVMCollector()  # Fallback
tech_analysis = TechnicalAnalysis()
fund_analysis = FundamentalAnalysis()
db = create_database()

# Cache pour les données (évite de rescraper à chaque requête)
data_cache = {}
companies_cache = None
companies_payload_cache = None
company_lookup_cache = None
palmares_cache = None
palmares_cache_expires_at = 0
PALMARES_CACHE_TTL_SECONDS = int(os.getenv('PALMARES_CACHE_TTL', '300'))
listed_companies_cache = None
listed_companies_cache_expires_at = 0
LISTED_COMPANIES_CACHE_TTL_SECONDS = int(os.getenv('LISTED_COMPANIES_CACHE_TTL', '300'))
COMPARE_DASHBOARD_CACHE_TTL_SECONDS = int(os.getenv('COMPARE_CACHE_TTL_SECONDS', '300'))
MARKET_SUMMARY_CACHE_TTL_SECONDS = int(os.getenv('MARKET_SUMMARY_CACHE_TTL', '120'))
HOME_CACHE_TTL_SECONDS = int(os.getenv('HOME_CACHE_TTL_SECONDS', '120'))
ANALYSIS_CACHE_TTL_SECONDS = int(os.getenv('ANALYSIS_CACHE_TTL_SECONDS', '1800'))
CACHE_BUILD_LOCK_SECONDS = int(os.getenv('CACHE_BUILD_LOCK_SECONDS', '120'))
compare_dashboard_cache = None
compare_dashboard_cache_expires_at = 0.0
brvm_logo_index_cache = None
company_info_scraper = None
COMPANY_LOGOS_PATH = os.path.join(os.path.dirname(__file__), 'data', 'company_logos.json')
COMPANY_SECTORS_PATH = os.path.join(os.path.dirname(__file__), 'data', 'company_sectors.json')
COMPANIES_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'companies_full.json')
company_sectors_index_cache = None


def invalidate_companies_caches():
    """Vide les caches mémoire après un nouveau scrape du dataset."""
    global companies_payload_cache, company_lookup_cache, companies_cache
    global listed_companies_cache, listed_companies_cache_expires_at
    global palmares_cache, palmares_cache_expires_at
    global compare_dashboard_cache, compare_dashboard_cache_expires_at
    global company_sectors_index_cache

    companies_payload_cache = None
    company_lookup_cache = None
    companies_cache = None
    company_sectors_index_cache = None
    compare_dashboard_cache = None
    compare_dashboard_cache_expires_at = 0.0
    listed_companies_cache = None
    listed_companies_cache_expires_at = 0
    palmares_cache = None
    palmares_cache_expires_at = 0
    data_cache.clear()
    invalidate_keys(
        CACHE_KEY_LISTED,
        CACHE_KEY_COMPARE,
        CACHE_KEY_PALMARES,
        CACHE_KEY_MARKET_SUMMARY,
        CACHE_KEY_HOME,
    )
    invalidate_pattern('analysis:')


def scrape_scheduler_disabled():
    return os.getenv('DISABLE_SCRAPE_SCHEDULER', '').lower() in ('1', 'true', 'yes')


def _live_external_fetch_enabled():
    """Scrapes Sikafinance / BRVM déclenchés par l'API (désactiver en prod SaaS)."""
    return os.getenv('ALLOW_LIVE_QUOTE_FETCH', 'true').lower() in ('1', 'true', 'yes')


def normalize_identifier(value):
    """Normalise un identifiant pour les recherches et correspondances."""
    return storage_normalize_identifier(value)


def derive_company_ticker(company):
    """Construit un ticker interne stable pour le dashboard."""
    return storage_derive_company_ticker(company)


def build_company_aliases(company):
    """Construit plusieurs alias pour retrouver une société facilement."""
    aliases = set()
    fields = [
        company.get('ticker'),
        company.get('symbol'),
        company.get('profile_name'),
        company.get('display_name'),
        company.get('legal_name'),
        company.get('brvm_reports_reference', {}).get('issuer'),
        company.get('market_quote', {}).get('name'),
    ]

    for field in fields:
        normalized = normalize_identifier(field)
        if normalized:
            aliases.add(normalized)

    return aliases


def company_richness(company):
    """Score simple pour préférer la fiche la plus complète."""
    return sum(
        1
        for key in [
            'symbol',
            'sector',
            'board_members',
            'shareholding',
            'financial_history',
            'market_quote',
            'brvm_profile_url',
            'brvm_reports_reference',
        ]
        if company.get(key)
    )


def merge_company_records(target, source):
    """Fusionne les champs manquants d'une fiche doublon dans la fiche principale."""
    for key, value in source.items():
        if value in (None, '', [], {}):
            continue

        if key not in target or target[key] in (None, '', [], {}):
            target[key] = value
            continue

        if isinstance(value, dict) and isinstance(target.get(key), dict):
            for child_key, child_value in value.items():
                if child_value not in (None, '', [], {}):
                    target[key].setdefault(child_key, child_value)


def records_match(left, right):
    """Détermine si deux fiches représentent probablement la même société."""
    left_aliases = build_company_aliases(left)
    right_aliases = build_company_aliases(right)

    if left_aliases & right_aliases:
        return True

    left_name = normalize_identifier(left.get('display_name') or left.get('profile_name'))
    right_name = normalize_identifier(right.get('display_name') or right.get('profile_name'))
    if left_name and right_name and (left_name in right_name or right_name in left_name):
        return True

    return False


def load_companies_payload():
    """Charge le dataset enrichi des sociétés si disponible."""
    global companies_payload_cache

    if companies_payload_cache is None:
        if not os.path.exists(COMPANIES_DATA_PATH):
            companies_payload_cache = {'companies': [], 'market_indices': []}
        else:
            with open(COMPANIES_DATA_PATH, 'r', encoding='utf-8') as file:
                companies_payload_cache = json.load(file)

    return companies_payload_cache


def get_company_records():
    """Retourne les sociétés enrichies filtrées pour le dashboard."""
    payload = load_companies_payload()
    companies = payload.get('companies', [])

    records = []
    for company in companies:
        ticker = derive_company_ticker(company)
        if not ticker:
            continue

        record = dict(company)
        record['ticker'] = ticker
        records.append(record)

    deduplicated = []
    for record in sorted(records, key=company_richness, reverse=True):
        existing = next((item for item in deduplicated if records_match(item, record)), None)
        if existing:
            merge_company_records(existing, record)
        else:
            deduplicated.append(record)

    return deduplicated


def build_company_lookup():
    """Construit un index des sociétés par alias/ticker."""
    global company_lookup_cache

    if company_lookup_cache is None:
        company_lookup_cache = {}
        for company in get_company_records():
            for alias in build_company_aliases(company):
                company_lookup_cache.setdefault(alias, company)
        for company in get_listed_company_records():
            for alias in build_company_aliases(company):
                company_lookup_cache.setdefault(alias, company)

    return company_lookup_cache


def find_company_for_sikafinance_quote(quote, lookup):
    """Associe une cotation Sikafinance à une fiche enrichie si possible."""
    code = quote.get('code')
    symbol = code.split('.', 1)[0] if code else None
    needles = [
        normalize_identifier(symbol),
        normalize_identifier(code),
        normalize_identifier(quote.get('name')),
    ]

    for needle in needles:
        if needle and needle in lookup:
            return dict(lookup[needle])

    return None


def _build_listed_company_records_from_quotes(quotes, all_records):
    lookup = {}
    for company in all_records:
        for alias in build_company_aliases(company):
            lookup.setdefault(alias, company)

    listed = []
    seen_codes = set()
    for quote in quotes:
        code = quote.get('code')
        if not code or code in seen_codes:
            continue
        seen_codes.add(code)

        company = find_company_for_sikafinance_quote(quote, lookup)
        if company:
            company = dict(company)
        else:
            symbol = code.split('.', 1)[0]
            company = {
                'display_name': quote.get('name'),
                'symbol': symbol,
            }

        company['market_quote'] = quote
        if not company.get('symbol'):
            company['symbol'] = code.split('.', 1)[0]

        ticker = derive_company_ticker(company) or normalize_identifier(company.get('symbol'))
        company['ticker'] = ticker
        listed.append(company)

    listed.sort(
        key=lambda item: (item.get('display_name') or item.get('profile_name') or '').upper()
    )
    listed = attach_sectors_to_companies(attach_logos_to_companies(listed))
    try:
        sync_quotes_from_company_records(listed, db=db)
    except Exception as exc:
        print(f"⚠️  Sync cours : {exc}")
    return listed


def _build_listed_company_records_fallback(all_records):
    fallback = [dict(record) for record in all_records if record.get('market_quote')]
    fallback.sort(
        key=lambda item: (item.get('display_name') or item.get('profile_name') or '').upper()
    )
    return attach_sectors_to_companies(attach_logos_to_companies(fallback))


def _build_listed_company_records():
    """Construit la liste cotée (appelé sous verrou cache)."""
    all_records = get_company_records()
    if _live_external_fetch_enabled():
        try:
            quotes = get_company_info_scraper().fetch_sikafinance_market_data()['quotes']
            return _build_listed_company_records_from_quotes(quotes, all_records)
        except Exception as exc:
            print(f"⚠️  Cotations live Sikafinance : {exc}")
    return _build_listed_company_records_fallback(all_records)


def get_listed_company_records():
    """
    Sociétés cotées à la BRVM : cache partagé (Redis), anti-stampede.
  """
    global listed_companies_cache, listed_companies_cache_expires_at

    payload, _state = get_or_build(
        CACHE_KEY_LISTED,
        LISTED_COMPANIES_CACHE_TTL_SECONDS,
        _build_listed_company_records,
        lock_seconds=CACHE_BUILD_LOCK_SECONDS,
    )
    listed_companies_cache = payload
    listed_companies_cache_expires_at = time.time() + LISTED_COMPANIES_CACHE_TTL_SECONDS
    return payload


def get_company_by_ticker(ticker):
    """Retrouve une société enrichie à partir d'un ticker interne."""
    return build_company_lookup().get(normalize_identifier(ticker))


def load_brvm_logo_index():
    """Charge l'index des logos BRVM (fichier local ou scrape annuaire)."""
    global brvm_logo_index_cache

    if brvm_logo_index_cache is not None:
        return brvm_logo_index_cache

    if os.path.exists(COMPANY_LOGOS_PATH):
        with open(COMPANY_LOGOS_PATH, 'r', encoding='utf-8') as file:
            brvm_logo_index_cache = json.load(file)
        return brvm_logo_index_cache

    try:
        brvm_logo_index_cache = get_company_info_scraper().fetch_brvm_logo_index()
        os.makedirs(os.path.dirname(COMPANY_LOGOS_PATH), exist_ok=True)
        with open(COMPANY_LOGOS_PATH, 'w', encoding='utf-8') as file:
            json.dump(brvm_logo_index_cache, file, ensure_ascii=False, indent=2)
    except Exception:
        brvm_logo_index_cache = {'by_profile_url': {}, 'by_name': {}}

    return brvm_logo_index_cache


def resolve_company_logo_url(company, logo_index=None):
    """Retrouve l'URL du logo d'une société."""
    if company.get('logo_url'):
        return company['logo_url']

    if logo_index is None:
        logo_index = load_brvm_logo_index()

    profile_url = company.get('brvm_profile_url')
    if profile_url:
        logo = logo_index.get('by_profile_url', {}).get(profile_url)
        if logo:
            return logo

    scraper = get_company_info_scraper()
    for field in [
        company.get('display_name'),
        company.get('profile_name'),
        company.get('name'),
        (company.get('market_quote') or {}).get('name'),
    ]:
        name_key = scraper._normalize_key(field)
        if name_key:
            logo = logo_index.get('by_name', {}).get(name_key)
            if logo:
                return logo

    return None


def attach_logos_to_companies(companies):
    """Ajoute logo_url à chaque société si disponible."""
    logo_index = load_brvm_logo_index()
    for company in companies:
        if not company.get('logo_url'):
            company['logo_url'] = resolve_company_logo_url(company, logo_index)
    return companies


def normalize_sector_lookup_key(value):
    """Normalise un libellé société/secteur pour la correspondance."""
    if not value:
        return None
    text = re.sub(r'\s+', ' ', str(value).replace('\xa0', ' ')).strip()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(char for char in text if not unicodedata.combining(char))
    text = text.upper()
    text = re.sub(r'[^A-Z0-9]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def load_company_sectors_index():
    """Charge l'index secteur officiel (référentiel BRVM fourni)."""
    global company_sectors_index_cache

    if company_sectors_index_cache is not None:
        return company_sectors_index_cache

    if not os.path.exists(COMPANY_SECTORS_PATH):
        company_sectors_index_cache = {'by_name': {}, 'by_symbol': {}}
        return company_sectors_index_cache

    with open(COMPANY_SECTORS_PATH, 'r', encoding='utf-8') as file:
        payload = json.load(file)

    by_name = {}
    for sector, names in payload.get('sectors', {}).items():
        for name in names:
            key = normalize_sector_lookup_key(name)
            if key:
                by_name[key] = sector

    by_symbol = {
        str(symbol).upper(): sector
        for symbol, sector in payload.get('symbol_aliases', {}).items()
    }

    company_sectors_index_cache = {'by_name': by_name, 'by_symbol': by_symbol}
    return company_sectors_index_cache


def resolve_company_sector(company):
    """Retrouve le secteur BRVM à partir du référentiel ou des données scrapées."""
    sector_index = load_company_sectors_index()

    symbol = (company.get('symbol') or '').upper()
    if symbol and symbol in sector_index['by_symbol']:
        return sector_index['by_symbol'][symbol]

    quote = company.get('market_quote') or {}
    code = quote.get('code')
    if code:
        code_symbol = code.split('.', 1)[0].upper()
        if code_symbol in sector_index['by_symbol']:
            return sector_index['by_symbol'][code_symbol]

    ticker = normalize_identifier(company.get('ticker'))
    if ticker and ticker in sector_index['by_symbol']:
        return sector_index['by_symbol'][ticker]

    candidates = [
        company.get('display_name'),
        company.get('profile_name'),
        company.get('legal_name'),
        quote.get('name'),
    ]

    for field in candidates:
        field_key = normalize_sector_lookup_key(field)
        if not field_key:
            continue

        if field_key in sector_index['by_name']:
            return sector_index['by_name'][field_key]

        for name_key, sector in sector_index['by_name'].items():
            if name_key in field_key or field_key in name_key:
                return sector

    return company.get('sector')


def attach_sectors_to_companies(companies):
    """Applique le secteur officiel à chaque société cotée."""
    for company in companies:
        company['sector'] = resolve_company_sector(company)
    return companies


def serialize_company_for_selector(company):
    """Réduit les données d'une société pour le sélecteur du dashboard."""
    quote = company.get('market_quote', {})
    display_name = company.get('display_name') or company.get('profile_name') or company.get('legal_name')
    symbol = company.get('symbol') or company.get('brvm_reports_reference', {}).get('issuer')
    if not symbol and quote.get('code'):
        symbol = quote['code'].split('.', 1)[0]

    return {
        'ticker': company['ticker'],
        'name': display_name or quote.get('name'),
        'symbol': symbol,
        'sector': resolve_company_sector(company),
        'price': quote.get('last'),
        'variation': quote.get('variation_pct'),
        'volume': quote.get('volume_shares'),
        'code': quote.get('code'),
        'listed': True,
    }


def get_latest_financial_snapshot(company):
    """Retourne la derniere année financière disponible dans le scraping."""
    history = company.get('financial_history') or []
    if not history:
        return None
    return max(history, key=lambda item: item.get('year', 0))


def parse_executive_from_governance_raw(raw_text):
    """Extrait PDG / PCA depuis le texte brut Sikafinance (format libre)."""
    from analysis.governance_parser import extract_executives_from_raw

    return extract_executives_from_raw(raw_text)


def build_company_profile_summary(company):
    """Résumé textuel pour la fiche entreprise."""
    if not company:
        return None

    if company.get('profile_summary'):
        return company['profile_summary']

    sector = resolve_company_sector(company)
    legal_name = company.get('legal_name') or company.get('display_name')
    address = company.get('address') or (company.get('sikafinance_profile') or {}).get('address')

    parts = []
    if legal_name and sector:
        parts.append(f"{legal_name} est une société cotée à la BRVM ({sector}).")
    elif legal_name:
        parts.append(f"{legal_name} est une société cotée à la BRVM.")
    if address:
        parts.append(f"Siège : {address}.")

    return ' '.join(parts) if parts else None


def build_governance_payload(company):
    """Masque la gouvernance si la fraîcheur n'est pas vérifiable/récente."""
    if not company:
        return {
            'reference_year': None,
            'is_stale': True,
            'note': "Données de gouvernance indisponibles.",
            'chairman': None,
            'chief_executive': None,
            'board_members': [],
        }

    from analysis.governance_parser import enrich_governance

    sikafinance_governance = enrich_governance(company.get('sikafinance_governance') or {})
    if sikafinance_governance.get('roles') or sikafinance_governance.get('raw'):
        chairman = sikafinance_governance.get('chairman')
        chief_executive = sikafinance_governance.get('chief_executive')
        if sikafinance_governance.get('roles') or chairman or chief_executive:
            board_members = [
                {
                    'name': role.get('name'),
                    'role': role.get('role'),
                    'structure': None,
                }
                for role in sikafinance_governance.get('roles', [])
                if role.get('name')
            ]
            return {
                'reference_year': pd.Timestamp.now().year,
                'is_stale': False,
                'note': "Gouvernance mise à jour récemment.",
                'chairman': chairman,
                'chief_executive': chief_executive,
                'board_members': board_members,
                'source': 'sikafinance',
                'source_url': company.get('market_quote', {}).get('details_url'),
            }

    reference_year = company.get('governance_reference_year')
    current_year = pd.Timestamp.now().year

    # Tant que la source n'expose pas explicitement une année de gouvernance récente,
    # on évite d'afficher des noms pouvant être obsolètes.
    is_stale = True
    if isinstance(reference_year, int):
        is_stale = reference_year < (current_year - 2)

    if is_stale:
        return {
            'reference_year': reference_year,
            'is_stale': True,
            'note': (
                "Les informations de gouvernance disponibles dans la source BRVM "
                "ne sont pas datées de façon suffisamment récente. Elles sont masquées "
                "pour éviter d'afficher des données obsolètes."
            ),
            'chairman': None,
            'chief_executive': None,
            'board_members': [],
            'source': 'brvm',
            'source_url': company.get('brvm_profile_url'),
        }

    return {
        'reference_year': reference_year,
        'is_stale': False,
        'note': None,
        'chairman': company.get('chairman'),
        'chief_executive': company.get('chief_executive'),
        'board_members': (company.get('board_members') or [])[:8],
        'source': 'brvm',
        'source_url': company.get('brvm_profile_url'),
    }


def get_company_info_scraper():
    global company_info_scraper
    if company_info_scraper is None:
        company_info_scraper = CompanyInfoScraper()
    return company_info_scraper


def ensure_company_sikafinance_profile(company):
    """Charge profil Sikafinance (gouvernance, titres, historique financier) si incomplet."""
    if not company:
        return company

    from analysis.governance_parser import enrich_governance

    profile = company.get('sikafinance_profile') or {}
    enriched_gov = enrich_governance(
        company.get('sikafinance_governance') or profile.get('governance') or {}
    )
    company['sikafinance_governance'] = enriched_gov

    has_market = bool((profile or {}).get('market_stats'))
    has_financials = bool((profile or {}).get('financial_statements'))
    has_shareholders = bool((profile or {}).get('shareholders'))
    has_governance = bool(
        enriched_gov.get('chief_executive')
        or enriched_gov.get('chairman')
        or enriched_gov.get('raw')
    )

    if has_market and has_financials and has_governance and has_shareholders:
        return company

    if not _live_external_fetch_enabled():
        return company

    details_url = (company.get('market_quote') or {}).get('details_url')
    if not details_url:
        return company

    try:
        profile = get_company_info_scraper().fetch_sikafinance_company_profile(details_url)
        company['sikafinance_profile'] = profile
        company['sikafinance_governance'] = enrich_governance(profile.get('governance') or {})
        if profile.get('address') and not company.get('address'):
            company['address'] = profile['address']
    except Exception as exc:
        company['sikafinance_profile_error'] = str(exc)

    return company


def serialize_palmares_mover(row):
    """Formate une ligne du palmarès Sikafinance pour le dashboard."""
    symbol = row.get('symbol')
    code = row.get('code')
    ticker = normalize_identifier(symbol) or normalize_identifier(code)

    company = get_company_by_ticker(ticker) if ticker else None
    if not company and row.get('name'):
        lookup = build_company_lookup()
        name_key = normalize_identifier(row['name'])
        if name_key:
            for alias, record in lookup.items():
                if name_key in alias or alias in name_key:
                    company = record
                    break

    if company:
        ticker = company['ticker']
        display_name = (
            company.get('display_name')
            or company.get('profile_name')
            or row.get('name')
        )
        symbol = company.get('symbol') or symbol
    else:
        display_name = row.get('name')
        ticker = ticker or symbol or code

    return {
        'ticker': ticker,
        'name': display_name,
        'symbol': symbol,
        'price': row.get('last'),
        'variation': row.get('variation_pct'),
        'volume': row.get('volume'),
        'source': 'sikafinance_palmares',
        'source_url': row.get('cotation_url'),
    }


def _build_sikafinance_palmares_movers():
    if not _live_external_fetch_enabled():
        raise RuntimeError('ALLOW_LIVE_QUOTE_FETCH désactivé')
    from storage.palmares_store import refresh_palmares_snapshot

    return refresh_palmares_snapshot(limit=int(os.getenv('PALMARES_FETCH_LIMIT', '30')))


def fetch_sikafinance_palmares_movers():
    """Charge hausses/baisses — live, cache Redis, ou snapshot fichier (week-end = vendredi)."""
    global palmares_cache, palmares_cache_expires_at

    if not _live_external_fetch_enabled():
        snapshot = load_palmares_snapshot()
        if snapshot and (snapshot.get('gainers') or snapshot.get('losers')):
            palmares_cache = snapshot
            return snapshot
        return palmares_cache or {'gainers': [], 'losers': []}

    try:
        payload, _state = get_or_build(
            CACHE_KEY_PALMARES,
            PALMARES_CACHE_TTL_SECONDS,
            _build_sikafinance_palmares_movers,
            lock_seconds=CACHE_BUILD_LOCK_SECONDS,
        )
        palmares_cache = payload
        palmares_cache_expires_at = time.time() + PALMARES_CACHE_TTL_SECONDS
        save_palmares_snapshot(payload)
        return payload
    except Exception as exc:
        print(f"⚠️  Palmarès Sikafinance : {exc}")
        snapshot = load_palmares_snapshot()
        if snapshot:
            return snapshot
        return palmares_cache or {'gainers': [], 'losers': []}


def get_market_indices():
    """Retourne les principaux indices BRVM du dataset scrappé (sans doublons)."""
    payload = load_companies_payload()
    indices = payload.get('market_indices', [])
    preferred_names = {
        'BRVM COMPOSITE',
        'BRVM 30',
        'BRVM - FINANCE',
        'BRVM - INDUSTRIE',
        'BRVM - TRANSPORT',
        'BRVM - TELECOMMUNICATIONS',
        'BRVM - SERVICES PUBLICS',
    }

    selected = []
    seen_names = set()
    for index in indices:
        name = index.get('name')
        if name not in preferred_names or name in seen_names:
            continue
        seen_names.add(name)
        selected.append(index)

    selected.sort(key=lambda item: item.get('name') or '')
    return selected


def _movers_from_quoted_companies(quoted_companies, limit=30):
    """Repli local : hausses/baisses à partir des cotations du dataset."""
    with_variation = [c for c in quoted_companies if c.get('variation') is not None]
    gainers = sorted(
        [c for c in with_variation if (c.get('variation') or 0) > 0],
        key=lambda item: item.get('variation', 0),
        reverse=True,
    )[:limit]
    losers = sorted(
        [c for c in with_variation if (c.get('variation') or 0) < 0],
        key=lambda item: item.get('variation', 0),
    )[:limit]
    return gainers, losers


def _build_market_summary_uncached():
    """Construit une vue globale légère du marché pour le dashboard."""
    companies = [serialize_company_for_selector(company) for company in get_listed_company_records()]
    quoted_companies = [company for company in companies if company.get('price') is not None]
    sectors = sorted({company['sector'] for company in companies if company.get('sector')})

    palmares_meta = {
        'source': 'dataset_fallback',
        'source_url': None,
        'fetched_at': None,
        'since': 'yesterday',
    }
    top_gainers = []
    top_losers = []
    try:
        palmares = fetch_sikafinance_palmares_movers()
        top_gainers = [
            serialize_palmares_mover(row) for row in palmares.get('gainers', [])
        ]
        top_losers = [
            serialize_palmares_mover(row) for row in palmares.get('losers', [])
        ]
        if top_gainers or top_losers:
            palmares_meta = {
                'source': 'sikafinance_palmares',
                'source_url': palmares.get('source_url'),
                'fetched_at': palmares.get('fetched_at'),
                'since': palmares.get('since', 'yesterday'),
            }
    except Exception as exc:
        palmares_meta['error'] = str(exc)

    if not top_gainers or not top_losers:
        fallback_gainers, fallback_losers = _movers_from_quoted_companies(quoted_companies)
        if not top_gainers:
            top_gainers = fallback_gainers
        if not top_losers:
            top_losers = fallback_losers
        if palmares_meta.get('source') != 'sikafinance_palmares':
            palmares_meta['source'] = 'dataset_fallback'

    advancing = sum(1 for company in quoted_companies if (company.get('variation') or 0) > 0)
    declining = sum(1 for company in quoted_companies if (company.get('variation') or 0) < 0)
    unchanged = sum(1 for company in quoted_companies if (company.get('variation') or 0) == 0)

    payload = load_companies_payload()
    return {
        'indices': get_market_indices(),
        'stats': {
            'companies_count': len(companies),
            'quoted_companies_count': len(quoted_companies),
            'sectors_count': len(sectors),
            'advancing_count': advancing,
            'declining_count': declining,
            'unchanged_count': unchanged,
        },
        'sectors': sectors,
        'top_gainers': top_gainers,
        'top_losers': top_losers,
        'palmares': palmares_meta,
        'generated_at': payload.get('generated_at'),
        'sources': payload.get('sources', {}),
    }


def build_market_summary():
    """Vue marché avec cache partagé."""
    payload, _state = get_or_build(
        CACHE_KEY_MARKET_SUMMARY,
        MARKET_SUMMARY_CACHE_TTL_SECONDS,
        _build_market_summary_uncached,
        lock_seconds=CACHE_BUILD_LOCK_SECONDS,
    )
    return payload


def build_companies_selector_list():
    records = get_listed_company_records()
    if records:
        items = [serialize_company_for_selector(company) for company in records]
        items.sort(key=lambda item: item['name'] or '')
        return items
    if companies_cache is not None:
        return companies_cache
    return scraper.get_all_listed_companies().to_dict('records')


def warm_api_caches():
    """Pré-chauffe les caches lourds (cron / worker)."""
    print('🔥 Pré-chauffage cache API…')
    get_listed_company_records()
    build_market_summary()
    get_compare_dashboard_payload()
    print('✅ Caches API prêts.')


@app.route('/api/health')
def api_health():
    """Santé API + cache."""
    return jsonify({
        'status': 'ok',
        'cache': cache_status(),
        'live_external_fetch': _live_external_fetch_enabled(),
        'scrape_scheduler_disabled': scrape_scheduler_disabled(),
        'palmares_scheduler': get_palmares_refresh_status(),
    })


@app.route('/api/home')
def api_home():
    """Accueil : sociétés + résumé marché (1 requête, cache partagé)."""

    def builder():
        return {
            'companies': build_companies_selector_list(),
            'market_summary': build_market_summary(),
        }

    payload, cache_state = get_or_build(
        CACHE_KEY_HOME,
        HOME_CACHE_TTL_SECONDS,
        builder,
        lock_seconds=CACHE_BUILD_LOCK_SECONDS,
    )
    response = jsonify(payload)
    response.headers['X-Cache-Status'] = cache_state
    return response


@app.route('/api/companies')
def get_companies():
    """API : Liste des sociétés cotées à la BRVM (cache, pas de scrape par requête)."""
    global companies_cache
    companies_cache = build_companies_selector_list()
    return jsonify(companies_cache)


def _compare_fetch_balance_sheets_enabled():
    return os.getenv('COMPARE_FETCH_BALANCE_SHEETS', 'false').lower() in ('1', 'true', 'yes')


def _build_compare_dashboard_payload():
    from analysis.company_compare import build_compare_dashboard

    records = get_listed_company_records()
    payload = build_compare_dashboard(
        records,
        db=db,
        enrich_balance_sheets=_compare_fetch_balance_sheets_enabled(),
    )
    payload['generated_at'] = datetime.now(timezone.utc).isoformat()
    payload['dataset_generated_at'] = load_companies_payload().get('generated_at')
    return payload


def get_compare_dashboard_payload():
    """Payload comparaison avec cache partagé (évite recalculs simultanés)."""
    global compare_dashboard_cache, compare_dashboard_cache_expires_at

    payload, _state = get_or_build(
        CACHE_KEY_COMPARE,
        COMPARE_DASHBOARD_CACHE_TTL_SECONDS,
        _build_compare_dashboard_payload,
        lock_seconds=CACHE_BUILD_LOCK_SECONDS,
    )
    compare_dashboard_cache = payload
    compare_dashboard_cache_expires_at = time.time() + COMPARE_DASHBOARD_CACHE_TTL_SECONDS
    result = dict(payload)
    result.pop('data_notes', None)
    return result


def _compare_profiles_same_sector(profiles):
    from analysis.company_compare import profiles_same_sector

    return profiles_same_sector(profiles)


@app.route('/api/compare/by-sector')
def compare_by_sector():
    """API : comparaison par secteur, classements et profils investisseur."""
    from analysis.company_compare import build_head_to_head

    payload = get_compare_dashboard_payload()

    tickers = request.args.getlist('tickers') or request.args.getlist('ticker')
    if len(tickers) == 2:
        lookup = payload.get('companies_by_ticker') or {}
        selected = [lookup.get(normalize_identifier(t)) for t in tickers]
        if all(selected):
            if not _compare_profiles_same_sector(selected):
                return jsonify({
                    'error': 'La comparaison est limitée aux sociétés du même secteur.',
                }), 400
            payload['head_to_head'] = build_head_to_head(selected)

    return jsonify(payload)


@app.route('/api/compare/head-to-head')
def compare_head_to_head():
    """API : comparaison détaillée entre deux sociétés du même secteur."""
    from analysis.company_compare import build_head_to_head

    tickers = request.args.getlist('tickers') or request.args.getlist('ticker')
    if len(tickers) != 2:
        return jsonify({'error': 'Indiquez exactement 2 tickers (ex. ?tickers=SIB&tickers=BOABF)'}), 400

    payload = get_compare_dashboard_payload()
    lookup = payload.get('companies_by_ticker') or {}
    profiles = [lookup.get(normalize_identifier(ticker)) for ticker in tickers]
    if not all(profiles):
        missing = [t for t, profile in zip(tickers, profiles) if not profile]
        return jsonify({'error': f'Société(s) introuvable(s) : {", ".join(missing)}'}), 404

    if not _compare_profiles_same_sector(profiles):
        sectors = sorted({(p or {}).get('sector') or 'Non classé' for p in profiles})
        return jsonify({
            'error': (
                'La comparaison est limitée aux sociétés du même secteur '
                f'(secteurs demandés : {", ".join(sectors)}).'
            ),
        }), 400

    head_to_head = build_head_to_head(profiles)
    if not head_to_head:
        return jsonify({'error': 'Impossible de comparer ces sociétés.'}), 400

    return jsonify({
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'head_to_head': head_to_head,
        'companies': {profile['ticker']: profile for profile in profiles},
    })


@app.route('/api/market-summary')
def market_summary():
    """API : Vue globale du marché BRVM pour le dashboard."""
    return jsonify(build_market_summary())

def _analysis_cache_key(ticker):
    return f"analysis:{normalize_identifier(ticker) or ticker}"


def _build_analysis_payload(ticker):
    """Calcule le payload d'analyse (sans réponse Flask)."""
    company = get_company_by_ticker(ticker)
    if company:
        company = ensure_company_sikafinance_profile(dict(company))

    source_ticker = company.get('symbol') if company else ticker
    market_quote = company.get('market_quote', {}) if company else {}

    if company:
        company_row = dict(company)
        company_row['ticker'] = ticker
        try:
            db.sync_company_quote(company_row)
        except Exception as exc:
            print(f"⚠️  Sync cours {ticker} : {exc}")

    def legacy_historical_fetch():
        legacy_df = scraper.get_historical_data(source_ticker, days=100)
        if legacy_df.empty:
            legacy_df = collector.get_historical_data(source_ticker, days=100)
        if not legacy_df.empty and market_quote:
            if market_quote.get('last') is not None:
                legacy_df.loc[legacy_df.index[-1], 'close'] = market_quote['last']
            if market_quote.get('volume_shares') is not None:
                legacy_df.loc[legacy_df.index[-1], 'volume'] = market_quote['volume_shares']
        return legacy_df

    df, price_history_meta = resolve_price_history(
        company,
        ticker,
        days=120,
        legacy_fetch=legacy_historical_fetch,
        db=db,
    )

    if df.empty:
        raise LookupError('Aucune donnée de marché disponible pour cette société.')

    df_analyzed, signal = tech_analysis.run_full_analysis(df)

    if market_quote.get('last') is not None:
        current_price = float(market_quote['last'])
        df_analyzed.loc[df_analyzed.index[-1], 'close'] = current_price
    else:
        current_price = float(df_analyzed.iloc[-1]['close'])

    fundamental = fund_analysis.get_fundamental_data(source_ticker, current_price)
    latest_financial = get_latest_financial_snapshot(company) if company else None
    if latest_financial:
        if latest_financial.get('revenue_mfcfa') is not None:
            fundamental['revenue'] = latest_financial['revenue_mfcfa'] * 1e6
        if latest_financial.get('net_income_mfcfa') is not None:
            fundamental['net_income'] = latest_financial['net_income_mfcfa'] * 1e6
    ratios = fund_analysis.get_financial_ratios(fundamental)

    latest = df_analyzed.iloc[-1]
    governance = build_governance_payload(company)

    from analysis.company_financials import build_financial_payload
    from analysis.company_shareholding import build_shareholding_payload

    financials = build_financial_payload(company) if company else build_financial_payload({})
    shareholding = build_shareholding_payload(company) if company else build_shareholding_payload({})

    return {
        'ticker': ticker,
        'current_price': round(current_price, 2),
        'signal': signal,
        'technical': {
            'rsi': round(latest['RSI'], 2),
            'macd': round(latest['MACD'], 2),
            'macd_signal': round(latest['MACD_signal'], 2),
            'sma_20': round(latest['SMA_20'], 2),
            'sma_50': round(latest['SMA_50'], 2),
            'bb_upper': round(latest['BB_upper'], 2),
            'bb_lower': round(latest['BB_lower'], 2),
        },
        'fundamental': {
            'revenue': round(fundamental['revenue'] / 1e9, 1),
            'net_income': round(fundamental['net_income'] / 1e9, 1),
            'eps': round(fundamental.get('eps', 0), 2),
            'pe_ratio': round(fundamental.get('pe_ratio', 0), 2),
            'dividend_yield': round(fundamental.get('dividend_yield', 0) * 100, 2),
            'outlook': fundamental.get('outlook', 'N/A'),
            'ratios': {
                'net_margin': round(ratios.get('net_margin', 0) * 100, 2),
                'roe': round(ratios.get('roe', 0) * 100, 2),
                'roa': round(ratios.get('roa', 0) * 100, 2),
            },
        },
        'company': {
            'name': company.get('display_name') if company else ticker,
            'legal_name': company.get('legal_name') if company else None,
            'symbol': company.get('symbol') if company else ticker,
            'sector': resolve_company_sector(company) if company else None,
            'listing_date': company.get('listing_date') if company else None,
            'profile_summary': build_company_profile_summary(company) if company else None,
            'capital_social': company.get('capital_social') if company else None,
            'address': company.get('address') if company else None,
            'postal_address': company.get('postal_address') if company else None,
            'email': company.get('email') if company else None,
            'phone': company.get('phone') if company else None,
            'fax': company.get('fax') if company else None,
            'website': (
                company.get('profile_website') or company.get('website')
            ) if company else None,
            'chairman': governance['chairman'],
            'chief_executive': governance['chief_executive'],
            'governance_raw': (company.get('sikafinance_governance') or {}).get('raw') if company else None,
            'governance_reference_year': governance['reference_year'],
            'governance_is_stale': governance['is_stale'],
            'governance_note': governance['note'],
            'governance_source': governance.get('source'),
            'governance_source_url': governance.get('source_url'),
            'profile_url': company.get('brvm_profile_url') if company else None,
            'report_url': company.get('brvm_reports_reference', {}).get('report_page_url') if company else None,
            'market_quote': market_quote,
            'board_members': governance['board_members'],
            'shareholding': shareholding,
            'financial_history': company.get('financial_history') if company else [],
            'market_stats': financials.get('market_stats'),
            'financial_statements': financials.get('statements', []),
        },
        'financials': financials,
        'historical_prices': df_analyzed[['date', 'open', 'high', 'low', 'close', 'volume']].tail(60).to_dict('records'),
        'technical_series': TechnicalAnalysis.serialize_series(df_analyzed, limit=60),
        'price_history': price_history_meta,
        'market_quote': {
            'last': market_quote.get('last'),
            'opening': market_quote.get('opening'),
            'high': market_quote.get('high'),
            'low': market_quote.get('low'),
            'variation_pct': market_quote.get('variation_pct'),
            'volume_shares': market_quote.get('volume_shares'),
            'previous_close': compute_previous_close(market_quote),
        },
        'last_updated': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'sources': load_companies_payload().get('sources', {}),
        'dataset_generated_at': load_companies_payload().get('generated_at'),
    }


@app.route('/api/analysis/<ticker>')
def get_analysis(ticker):
    """API : Analyse complète pour un ticker (cache partagé)."""
    cache_key = _analysis_cache_key(ticker)

    try:
        result, cache_state = get_or_build(
            cache_key,
            ANALYSIS_CACHE_TTL_SECONDS,
            lambda: _build_analysis_payload(ticker),
            lock_seconds=min(CACHE_BUILD_LOCK_SECONDS, 90),
        )
        response = jsonify(result)
        response.headers['X-Cache-Status'] = cache_state
        return response
    except LookupError as exc:
        return jsonify({'error': str(exc)}), 404
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/refresh/<ticker>')
def refresh_analysis(ticker):
    """Force le rafraîchissement des données (rate limit recommandé côté client)."""
    cache_delete(_analysis_cache_key(ticker))
    legacy_key = f"{ticker}_analysis"
    if legacy_key in data_cache:
        del data_cache[legacy_key]
    return get_analysis(ticker)

@app.route('/api/market-overview')
def market_overview():
    """Vue d'ensemble du marché"""
    return jsonify(build_market_summary())


@app.route('/api/dataset-status')
def dataset_status():
    """État du dataset local et du planificateur de scrape."""
    payload = load_companies_payload()
    status = {
        'dataset_generated_at': payload.get('generated_at'),
        'companies_count': payload.get('companies_count'),
        'quotes_count': payload.get('quotes_count'),
        'database_engine': getattr(db, 'engine', 'sqlite'),
        'database_uri': getattr(db, 'db_path', None),
        'stock_prices_count': db.count_all_stock_prices(),
        'companies_in_database': db.count_companies() if hasattr(db, 'count_companies') else None,
        'scrape_interval_hours': float(os.getenv('SCRAPE_INTERVAL_HOURS', '2')),
        'scheduler': get_scrape_status(),
        'scrape_scheduler_disabled': scrape_scheduler_disabled(),
        'worker_hint': (
            'Scrape externe : python scrape_companies.py ou python scripts/run_scrape_worker.py'
            if scrape_scheduler_disabled()
            else None
        ),
    }
    if get_db_engine() == 'mysql':
        status['users_count'] = User.query.count()
        status['subscription_plans_count'] = SubscriptionPlan.query.count()
    return jsonify(status)


@app.route('/api/prices/<ticker>')
def get_price_history(ticker):
    """Historique des cours en base pour un ticker."""
    normalized = normalize_identifier(ticker)
    if not normalized:
        return jsonify({'error': 'Ticker invalide'}), 400

    company = get_company_by_ticker(normalized)
    if company:
        company_row = dict(company)
        company_row['ticker'] = normalized
        db.sync_company_quote(company_row)

    days = int(request.args.get('days', 120))
    history = db.get_stock_prices(normalized, days=days)
    first_date, last_date = db.get_price_date_range(normalized)

    return jsonify({
        'ticker': normalized,
        'sessions': len(history),
        'first_date': first_date,
        'last_date': last_date,
        'prices': history.to_dict('records'),
    })


def frontend_built():
    return os.path.isfile(os.path.join(FRONTEND_DIST, 'index.html'))


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Sert le build React en production (après toutes les routes /api/*)."""
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404

    if frontend_built():
        if path and os.path.isfile(os.path.join(FRONTEND_DIST, path)):
            return send_from_directory(FRONTEND_DIST, path)
        return send_from_directory(FRONTEND_DIST, 'index.html')

    return jsonify({
        'message': 'API BRVM active. Frontend React non buildé.',
        'hint': 'cd frontend && npm install && npm run build',
        'dev_hint': 'En dev : npm run dev dans frontend/ (port 5173)',
        'api': {
            'companies': '/api/companies',
            'market_summary': '/api/market-summary',
            'analysis': '/api/analysis/<ticker>',
            'refresh': '/api/refresh/<ticker>',
        },
    })


@app.before_request
def _before_api_request():
    """Rate limit + planificateur scrape (si activé)."""
    rate_error = check_request_limit(request)
    if rate_error:
        response = jsonify(rate_error)
        response.status_code = 429
        response.headers['Retry-After'] = str(rate_error.get('retry_after_seconds', 60))
        return response

    if not scrape_scheduler_disabled():
        start_scrape_scheduler(on_complete=_on_scrape_complete)
    start_palmares_scheduler()


def _on_scrape_complete():
    from jobs.post_scrape import run_post_scrape_hooks

    run_post_scrape_hooks()


if __name__ == '__main__':
    if not scrape_scheduler_disabled():
        start_scrape_scheduler(on_complete=_on_scrape_complete)
    else:
        print('⏸️  API sans planificateur scrape (DISABLE_SCRAPE_SCHEDULER).')
        print('   Worker : python scripts/run_scrape_worker.py')
    start_palmares_scheduler()
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    port = int(os.getenv('PORT', '5050'))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)