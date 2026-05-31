"""
Profils de comparaison, scores investisseur et classements (données BRVM / cotations).
"""
import json
import os

from analysis.balance_sheet_parser import get_latest_balance_sheet
from analysis.company_financials import get_financial_statements, get_market_stats
from analysis.price_history import resolve_price_history

UNKNOWN_SECTOR = "Non classé"

_COMPANY_SECTORS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "company_sectors.json",
)
_sector_display_order_cache = None


def load_sector_display_order():
    """Ordre d'affichage des secteurs (référentiel BRVM)."""
    global _sector_display_order_cache

    if _sector_display_order_cache is not None:
        return _sector_display_order_cache

    if not os.path.exists(_COMPANY_SECTORS_PATH):
        _sector_display_order_cache = []
        return _sector_display_order_cache

    with open(_COMPANY_SECTORS_PATH, "r", encoding="utf-8") as file:
        payload = json.load(file)

    order = list(payload.get("sector_order") or [])
    if UNKNOWN_SECTOR not in order:
        order.append(UNKNOWN_SECTOR)
    _sector_display_order_cache = order
    return _sector_display_order_cache


def sector_sort_key(sector_name):
    order = load_sector_display_order()
    name = sector_name or UNKNOWN_SECTOR
    try:
        return (order.index(name), name)
    except ValueError:
        return (len(order), name)

SCORE_WEIGHTS = {
    "profitability": 0.25,
    "growth": 0.20,
    "dividends": 0.20,
    "valuation": 0.15,
    "market": 0.20,
}

HIGHER_IS_BETTER = {
    "revenue_mfcfa",
    "net_income_mfcfa",
    "revenue_growth_pct",
    "net_income_growth_pct",
    "revenue_growth_5y_pct",
    "net_income_growth_5y_pct",
    "eps_growth_5y_pct",
    "dividend_growth_5y_pct",
    "net_margin_pct",
    "eps_fcfa",
    "dividend_per_share_fcfa",
    "dividend_yield_pct",
    "market_cap_mfcfa",
    "perf_1m_pct",
    "perf_3m_pct",
    "perf_6m_pct",
    "perf_1y_pct",
    "variation",
    "investor_score",
}

LOWER_IS_BETTER = {"pe_ratio", "payout_ratio_pct", "debt_to_equity_pct"}


def _display_name(company):
    quote = company.get("market_quote") or {}
    return (
        company.get("display_name")
        or company.get("profile_name")
        or company.get("legal_name")
        or quote.get("name")
        or company.get("ticker")
    )


def _symbol(company):
    quote = company.get("market_quote") or {}
    symbol = company.get("symbol") or company.get("ticker")
    if not symbol and quote.get("code"):
        symbol = quote["code"].split(".", 1)[0]
    return symbol


def _safe_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round(value, digits=2):
    if value is None:
        return None
    return round(float(value), digits)


def _growth_between(years_map, start_year, end_year):
    start = years_map.get(start_year)
    end = years_map.get(end_year)
    if start is None or end is None or start == 0:
        return None
    return _round((end - start) / abs(start) * 100)


def _years_map(statements, field):
    return {
        row.get("year"): _safe_float(row.get(field))
        for row in statements
        if row.get("year") is not None and row.get(field) is not None
    }


GROWTH_CAGR_YEARS = 5


def _cagr_pct(years_map, start_year, end_year):
    """CAGR annualisé entre deux exercices (repli sur variation totale si signes négatifs)."""
    start = years_map.get(start_year)
    end = years_map.get(end_year)
    if start is None or end is None:
        return None

    year_span = end_year - start_year
    if year_span <= 0:
        return None

    if start == 0:
        return None

    if start < 0 or end < 0:
        return _growth_between(years_map, start_year, end_year)

    ratio = end / start
    if ratio <= 0:
        return None

    if year_span == 1:
        return _growth_between(years_map, start_year, end_year)

    try:
        return _round((ratio ** (1 / year_span) - 1) * 100)
    except (ValueError, ZeroDivisionError, OverflowError):
        return _growth_between(years_map, start_year, end_year)


def compute_multi_year_growth(statements, span_years=GROWTH_CAGR_YEARS):
    """CAGR sur 5 exercices (ou moins si historique plus court)."""
    if len(statements) < 2:
        return {}

    ordered = sorted(statements, key=lambda item: item.get("year") or 0)
    years = [item.get("year") for item in ordered if item.get("year")]
    if len(years) < 2:
        return {}

    end_year = years[-1]
    start_year = years[-span_years] if len(years) >= span_years else years[0]
    year_span = end_year - start_year

    revenue = _years_map(ordered, "revenue_mfcfa")
    net_income = _years_map(ordered, "net_income_mfcfa")
    eps = _years_map(ordered, "eps_fcfa")
    dividend = _years_map(ordered, "dividend_per_share_fcfa")

    return {
        "revenue_growth_5y_pct": _cagr_pct(revenue, start_year, end_year),
        "net_income_growth_5y_pct": _cagr_pct(net_income, start_year, end_year),
        "eps_growth_5y_pct": _cagr_pct(eps, start_year, end_year),
        "dividend_growth_5y_pct": _cagr_pct(dividend, start_year, end_year),
        "growth_span_years": year_span,
        "growth_start_year": start_year,
        "growth_end_year": end_year,
    }


def compute_price_performance(company, ticker, db=None):
    """Performances boursières si historique réel en base."""
    df, meta = resolve_price_history(
        company, ticker, days=280, db=db, ensure_history=False
    )
    if df.empty or meta.get("source") not in ("database",):
        return {
            "price_performance_reliable": False,
            "perf_1m_pct": None,
            "perf_3m_pct": None,
            "perf_6m_pct": None,
            "perf_1y_pct": None,
            "high_52w": None,
            "low_52w": None,
        }

    frame = df.sort_values("date")
    closes = frame["close"].astype(float)
    current = float(closes.iloc[-1])

    def perf_sessions(sessions):
        if len(closes) <= sessions:
            return None
        base = float(closes.iloc[-1 - sessions])
        if base == 0:
            return None
        return _round((current - base) / base * 100)

    return {
        "price_performance_reliable": True,
        "perf_1m_pct": perf_sessions(22),
        "perf_3m_pct": perf_sessions(66),
        "perf_6m_pct": perf_sessions(132),
        "perf_1y_pct": perf_sessions(252) if len(closes) > 252 else perf_sessions(len(closes) - 1),
        "high_52w": _round(closes.max()),
        "low_52w": _round(closes.min()),
    }


def build_comparison_profile(company, sector=None, db=None):
    """Profil complet pour comparaison et score."""
    quote = company.get("market_quote") or {}
    if quote.get("last") is None and quote.get("variation_pct") is None:
        return None

    statements = get_financial_statements(company)
    latest = statements[0] if statements else None
    market_stats = get_market_stats(company) or {}
    growth = compute_multi_year_growth(statements)

    price = _safe_float(quote.get("last"))
    eps = _safe_float(latest.get("eps_fcfa")) if latest else None
    dividend = _safe_float(latest.get("dividend_per_share_fcfa")) if latest else None
    revenue = _safe_float(latest.get("revenue_mfcfa")) if latest else None
    net_income = _safe_float(latest.get("net_income_mfcfa")) if latest else None

    pe_ratio = _safe_float(latest.get("pe_ratio")) if latest else None
    if pe_ratio is None and price and eps:
        pe_ratio = _round(price / eps) if eps else None

    net_margin_pct = None
    if revenue and net_income is not None and revenue != 0:
        net_margin_pct = _round(net_income / revenue * 100)

    dividend_yield_pct = None
    payout_ratio_pct = None
    if price and dividend:
        dividend_yield_pct = _round(dividend / price * 100)
    if eps and dividend and eps != 0:
        payout_ratio_pct = _round(dividend / eps * 100)

    ticker = company.get("ticker")
    price_perf = compute_price_performance(company, ticker, db=db)

    dividend_history = [
        {
            "year": row.get("year"),
            "dividend_per_share_fcfa": row.get("dividend_per_share_fcfa"),
        }
        for row in sorted(statements, key=lambda item: item.get("year") or 0)
        if row.get("dividend_per_share_fcfa") is not None
    ][-5:]

    balance_sheet = get_latest_balance_sheet(company)
    total_assets_mfcfa = balance_sheet.get("total_assets_mfcfa") if balance_sheet else None
    equity_mfcfa = balance_sheet.get("equity_mfcfa") if balance_sheet else None
    debt_mfcfa = balance_sheet.get("debt_mfcfa") if balance_sheet else None

    roe_pct = None
    roa_pct = None
    debt_to_equity_pct = None
    price_to_book = None

    if net_income is not None and equity_mfcfa:
        roe_pct = _round(net_income / equity_mfcfa * 100)
    if net_income is not None and total_assets_mfcfa:
        roa_pct = _round(net_income / total_assets_mfcfa * 100)
    if debt_mfcfa is not None and equity_mfcfa:
        debt_to_equity_pct = _round(debt_mfcfa / equity_mfcfa * 100)
    market_cap = market_stats.get("market_cap_mfcfa")
    if market_cap and equity_mfcfa:
        price_to_book = _round(market_cap / equity_mfcfa, 2)

    profile = {
        "ticker": ticker,
        "name": _display_name(company),
        "symbol": _symbol(company),
        "code": quote.get("code"),
        "sector": sector or company.get("sector") or UNKNOWN_SECTOR,
        "price": price,
        "variation": quote.get("variation_pct"),
        "volume": quote.get("volume_shares"),
        "opening": quote.get("opening"),
        "high": quote.get("high"),
        "low": quote.get("low"),
        "market_cap_mfcfa": market_cap,
        "float_pct": market_stats.get("float_pct"),
        "shares_outstanding": market_stats.get("shares_outstanding"),
        "financial_year": latest.get("year") if latest else None,
        "balance_sheet_year": balance_sheet.get("year") if balance_sheet else None,
        "revenue_mfcfa": revenue,
        "net_income_mfcfa": net_income,
        "revenue_growth_pct": latest.get("revenue_growth_pct") if latest else None,
        "net_income_growth_pct": latest.get("net_income_growth_pct") if latest else None,
        "eps_fcfa": eps,
        "pe_ratio": pe_ratio,
        "dividend_per_share_fcfa": dividend,
        "dividend_yield_pct": dividend_yield_pct,
        "payout_ratio_pct": payout_ratio_pct,
        "net_margin_pct": net_margin_pct,
        "dividend_history": dividend_history,
        "financial_statements_count": len(statements),
        "roe_pct": roe_pct,
        "roa_pct": roa_pct,
        "total_assets_mfcfa": total_assets_mfcfa,
        "equity_mfcfa": equity_mfcfa,
        "debt_mfcfa": debt_mfcfa,
        "debt_to_equity_pct": debt_to_equity_pct,
        "price_to_book": price_to_book,
        "balance_sheet_source": balance_sheet.get("source") if balance_sheet else None,
        "investor_score": None,
        "recommendation": None,
    }
    profile.update(growth)
    profile.update(price_perf)
    return profile


def _percentile_rank(value, values, higher_is_better=True):
    clean = [item for item in values if item is not None]
    if value is None or not clean:
        return None
    if higher_is_better:
        better = sum(1 for item in clean if item <= value)
    else:
        better = sum(1 for item in clean if item >= value)
    return round(better / len(clean) * 100, 1)


def _component_score(profile, peers, metrics, higher_is_better=True):
    ranks = []
    for metric in metrics:
        value = profile.get(metric)
        peer_values = [peer.get(metric) for peer in peers]
        rank = _percentile_rank(value, peer_values, higher_is_better=higher_is_better)
        if rank is not None:
            ranks.append(rank)
    if not ranks:
        return None
    return round(sum(ranks) / len(ranks), 1)


def assign_investor_scores(profiles):
    """Score 0-100 et recommandation, calculés par rapport au secteur."""
    by_sector = {}
    for profile in profiles:
        by_sector.setdefault(profile.get("sector") or UNKNOWN_SECTOR, []).append(profile)

    for peers in by_sector.values():
        for profile in peers:
            profitability = _component_score(
                profile,
                peers,
                ["net_margin_pct", "net_income_growth_pct", "roe_pct"],
            )
            solidity = _component_score(
                profile,
                peers,
                ["debt_to_equity_pct"],
                higher_is_better=False,
            )
            growth = _component_score(
                profile,
                peers,
                ["revenue_growth_5y_pct", "net_income_growth_5y_pct", "eps_growth_5y_pct"],
            )
            dividends = _component_score(
                profile,
                peers,
                ["dividend_yield_pct", "dividend_growth_5y_pct"],
            )
            valuation = _component_score(
                profile, peers, ["pe_ratio"], higher_is_better=False
            )

            market_metrics = ["variation"]
            if profile.get("price_performance_reliable"):
                market_metrics = ["perf_1y_pct", "perf_6m_pct", "perf_3m_pct"]
            market = _component_score(profile, peers, market_metrics)

            if solidity is not None:
                parts = [
                    (profitability, SCORE_WEIGHTS["profitability"] * 0.85),
                    (growth, SCORE_WEIGHTS["growth"] * 0.85),
                    (dividends, SCORE_WEIGHTS["dividends"] * 0.85),
                    (valuation, SCORE_WEIGHTS["valuation"] * 0.85),
                    (market, SCORE_WEIGHTS["market"] * 0.85),
                    (solidity, 0.15),
                ]
            else:
                parts = [
                    (profitability, SCORE_WEIGHTS["profitability"]),
                    (growth, SCORE_WEIGHTS["growth"]),
                    (dividends, SCORE_WEIGHTS["dividends"]),
                    (valuation, SCORE_WEIGHTS["valuation"]),
                    (market, SCORE_WEIGHTS["market"]),
                ]
            available = [(score, weight) for score, weight in parts if score is not None]
            if not available:
                profile["investor_score"] = None
                profile["recommendation"] = "neutral"
                profile["score_breakdown"] = {}
                continue

            total_weight = sum(weight for _, weight in available)
            score = sum(part * weight for part, weight in available) / total_weight
            profile["investor_score"] = round(score, 1)
            profile["score_breakdown"] = {
                "profitability": profitability,
                "growth": growth,
                "dividends": dividends,
                "valuation": valuation,
                "market": market,
                "solidity": solidity,
            }

            if score >= 70:
                profile["recommendation"] = "attractive"
            elif score >= 45:
                profile["recommendation"] = "neutral"
            else:
                profile["recommendation"] = "watch"


def _ranking_entry(profile, metric, rank):
    return {
        "rank": rank,
        "ticker": profile.get("ticker"),
        "name": profile.get("name"),
        "symbol": profile.get("symbol"),
        "sector": profile.get("sector"),
        "value": profile.get(metric),
    }


def build_rankings(profiles, metric, *, higher_is_better=True, limit=10):
    rows = [profile for profile in profiles if profile.get(metric) is not None]
    rows.sort(
        key=lambda item: item.get(metric),
        reverse=higher_is_better,
    )
    return [_ranking_entry(row, metric, index + 1) for index, row in enumerate(rows[:limit])]


def build_sector_rankings(companies):
    """Classements internes au secteur pour chaque critère."""
    metrics = [
        ("dividend_yield_pct", True),
        ("revenue_growth_5y_pct", True),
        ("net_margin_pct", True),
        ("perf_1y_pct", True),
        ("pe_ratio", False),
        ("variation", True),
    ]
    rankings = {}
    for metric, higher in metrics:
        key = metric
        if metric == "pe_ratio":
            key = "valuation_pe"
        elif metric == "dividend_yield_pct":
            key = "dividend_yield"
        elif metric == "revenue_growth_5y_pct":
            key = "growth_revenue_5y"
        elif metric == "net_margin_pct":
            key = "profitability_margin"
        elif metric == "perf_1y_pct":
            key = "market_performance_1y"
        elif metric == "variation":
            key = "market_variation_day"

        rankings[key] = build_rankings(companies, metric, higher_is_better=higher, limit=len(companies))
    return rankings


def profiles_same_sector(profiles):
    """Vrai si toutes les sociétés appartiennent au même secteur."""
    sectors = {(profile or {}).get("sector") or UNKNOWN_SECTOR for profile in profiles or [] if profile}
    return len(sectors) <= 1


def build_head_to_head(profiles):
    """Comparaison détaillée entre 2 sociétés du même secteur."""
    if len(profiles) != 2:
        return None
    if not profiles_same_sector(profiles):
        return None

    left, right = profiles[0], profiles[1]
    criteria = [
        ("revenue_mfcfa", "Chiffre d'affaires (M FCFA)", True),
        ("net_income_mfcfa", "Résultat net (M FCFA)", True),
        ("revenue_growth_pct", "Croissance CA (dernier ex.)", True),
        ("net_income_growth_pct", "Croissance résultat net", True),
        ("revenue_growth_5y_pct", "Croissance CA (CAGR 5 ans)", True),
        ("net_income_growth_5y_pct", "Croissance RN (CAGR 5 ans)", True),
        ("net_margin_pct", "Marge nette", True),
        ("eps_fcfa", "BPA", True),
        ("dividend_per_share_fcfa", "Dividende / action", True),
        ("dividend_yield_pct", "Rendement dividende", True),
        ("payout_ratio_pct", "Taux de distribution", False),
        ("pe_ratio", "PER", False),
        ("total_assets_mfcfa", "Total actif (M FCFA)", True),
        ("equity_mfcfa", "Capitaux propres (M FCFA)", True),
        ("debt_mfcfa", "Dettes (M FCFA)", False),
        ("debt_to_equity_pct", "Dette / capitaux propres", False),
        ("roe_pct", "ROE", True),
        ("roa_pct", "ROA", True),
        ("price_to_book", "Price-to-Book", False),
        ("price", "Cours actuel", None),
        ("perf_1y_pct", "Performance 1 an", True),
        ("perf_6m_pct", "Performance 6 mois", True),
        ("perf_3m_pct", "Performance 3 mois", True),
        ("perf_1m_pct", "Performance 1 mois", True),
        ("market_cap_mfcfa", "Capitalisation", True),
        ("investor_score", "Score investisseur", True),
    ]

    rows = []
    left_wins = 0
    right_wins = 0

    for key, label, higher_is_better in criteria:
        lv = left.get(key)
        rv = right.get(key)
        winner = None
        if lv is not None and rv is not None and lv != rv:
            if higher_is_better is None:
                winner = "tie"
            elif higher_is_better:
                winner = left["ticker"] if lv > rv else right["ticker"]
            else:
                winner = left["ticker"] if lv < rv else right["ticker"]
            if winner == left["ticker"]:
                left_wins += 1
            elif winner == right["ticker"]:
                right_wins += 1

        rows.append(
            {
                "key": key,
                "label": label,
                "left": lv,
                "right": rv,
                "winner": winner,
            }
        )

    return {
        "left": {"ticker": left["ticker"], "name": left["name"], "investor_score": left.get("investor_score")},
        "right": {"ticker": right["ticker"], "name": right["name"], "investor_score": right.get("investor_score")},
        "criteria": rows,
        "summary": {
            "left_wins": left_wins,
            "right_wins": right_wins,
            "ties": len(rows) - left_wins - right_wins,
        },
    }


def _enrich_balance_sheet_if_missing(company, scraper=None):
    """Charge le bilan BRVM à la volée si absent (fiche rapports disponible)."""
    if not company or company.get("balance_sheet_history"):
        return company

    reference = company.get("brvm_reports_reference") or {}
    report_page_url = reference.get("report_page_url")
    if not report_page_url:
        return company

    if scraper is None:
        from collectors.company_info_scraper import CompanyInfoScraper

        scraper = CompanyInfoScraper()

    scraper._attach_brvm_balance_sheet(company, reference)
    return company


def build_compare_dashboard(companies, db=None, scraper=None, enrich_balance_sheets=False):
    profiles = []
    for company in companies or []:
        company = dict(company)
        if enrich_balance_sheets:
            company = _enrich_balance_sheet_if_missing(company, scraper=scraper)
        sector = company.get("sector") or UNKNOWN_SECTOR
        profile = build_comparison_profile(company, sector=sector, db=db)
        if profile:
            profiles.append(profile)

    assign_investor_scores(profiles)

    groups = {}
    for profile in profiles:
        groups.setdefault(profile["sector"], []).append(profile)

    sectors = []
    for sector_name, items in groups.items():
        items.sort(
            key=lambda item: (
                item.get("investor_score") is None,
                -(item.get("investor_score") or 0),
                (item.get("name") or "").upper(),
            )
        )
        variations = [item["variation"] for item in items if item.get("variation") is not None]
        avg_variation = round(sum(variations) / len(variations), 2) if variations else None

        sectors.append(
            {
                "sector": sector_name,
                "companies_count": len(items),
                "avg_variation_pct": avg_variation,
                "advancing_count": sum(1 for value in variations if value > 0),
                "declining_count": sum(1 for value in variations if value < 0),
                "unchanged_count": sum(1 for value in variations if value == 0),
                "companies": items,
                "rankings": build_sector_rankings(items),
            }
        )

    sectors.sort(key=lambda item: sector_sort_key(item["sector"]))

    companies_by_ticker = {profile["ticker"]: profile for profile in profiles}

    return {
        "sectors": sectors,
        "sectors_count": len(sectors),
        "quoted_companies_count": len(profiles),
        "companies_by_ticker": companies_by_ticker,
        "metric_groups": [
            {
                "id": "financial",
                "title": "Indicateurs financiers",
                "metrics": [
                    {"key": "revenue_mfcfa", "label": "Chiffre d'affaires (M FCFA)"},
                    {"key": "net_income_mfcfa", "label": "Résultat net (M FCFA)"},
                    {"key": "revenue_growth_pct", "label": "Croissance CA"},
                    {"key": "net_income_growth_pct", "label": "Croissance RN"},
                    {"key": "revenue_growth_5y_pct", "label": "Croissance CA (CAGR 5 ans)"},
                    {"key": "net_margin_pct", "label": "Marge nette"},
                    {"key": "eps_fcfa", "label": "BPA"},
                ],
            },
            {
                "id": "market",
                "title": "Performance boursière",
                "metrics": [
                    {"key": "price", "label": "Cours"},
                    {"key": "variation", "label": "Variation jour"},
                    {"key": "perf_1m_pct", "label": "Perf. 1 mois"},
                    {"key": "perf_3m_pct", "label": "Perf. 3 mois"},
                    {"key": "perf_6m_pct", "label": "Perf. 6 mois"},
                    {"key": "perf_1y_pct", "label": "Perf. 1 an"},
                    {"key": "high_52w", "label": "Plus haut (historique)"},
                    {"key": "low_52w", "label": "Plus bas (historique)"},
                    {"key": "market_cap_mfcfa", "label": "Capitalisation"},
                ],
            },
            {
                "id": "dividends",
                "title": "Dividendes",
                "metrics": [
                    {"key": "dividend_per_share_fcfa", "label": "Dividende / action"},
                    {"key": "dividend_yield_pct", "label": "Rendement"},
                    {"key": "payout_ratio_pct", "label": "Taux de distribution"},
                ],
            },
            {
                "id": "valuation",
                "title": "Valorisation",
                "metrics": [
                    {"key": "pe_ratio", "label": "PER"},
                    {"key": "price_to_book", "label": "P/B"},
                    {"key": "market_cap_mfcfa", "label": "Capitalisation"},
                ],
            },
            {
                "id": "solidity",
                "title": "Solidité financière",
                "metrics": [
                    {"key": "total_assets_mfcfa", "label": "Total actif (M FCFA)"},
                    {"key": "equity_mfcfa", "label": "Capitaux propres (M FCFA)"},
                    {"key": "debt_mfcfa", "label": "Dettes (M FCFA)"},
                    {"key": "debt_to_equity_pct", "label": "Dette / CP"},
                    {"key": "roe_pct", "label": "ROE"},
                    {"key": "roa_pct", "label": "ROA"},
                ],
            },
        ],
        "score_weights": SCORE_WEIGHTS,
    }
