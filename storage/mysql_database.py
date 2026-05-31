"""Backend MySQL via SQLAlchemy."""

from datetime import date, datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import func, select

from storage.models import (
    Company,
    CompanyFinancial,
    MarketIndex,
    ScrapeRun,
    StockPrice,
    db,
)


class MySQLDatabase:
    """Accès MySQL : marché, utilisateurs et abonnements."""

    def __init__(self):
        self.engine = "mysql"

    @property
    def db_path(self):
        return db.engine.url.render_as_string(hide_password=True)

    def _parse_trade_date(self, trade_date):
        if isinstance(trade_date, date):
            return trade_date
        return datetime.strptime(str(trade_date)[:10], "%Y-%m-%d").date()

    def upsert_company(self, company):
        ticker = company.get("ticker")
        if not ticker:
            return

        quote = company.get("market_quote") or {}
        symbol = company.get("symbol")
        if not symbol and quote.get("code"):
            symbol = quote["code"].split(".", 1)[0]

        row = db.session.get(Company, ticker)
        if row is None:
            row = Company(ticker=ticker)
            db.session.add(row)

        row.symbol = symbol
        row.name = (
            company.get("display_name")
            or company.get("profile_name")
            or company.get("legal_name")
        )
        row.legal_name = company.get("legal_name")
        row.sector = company.get("sector")
        row.listing_date = company.get("listing_date")
        row.brvm_profile_url = company.get("brvm_profile_url")
        row.sikafinance_code = quote.get("code")
        row.website = company.get("website") or company.get("profile_website")
        row.address = company.get("address") or (company.get("sikafinance_profile") or {}).get(
            "address"
        )
        row.email = company.get("email")
        row.phone = company.get("phone")
        row.profile_summary = company.get("profile_summary")
        row.raw_payload = company

        for entry in company.get("financial_history") or []:
            year = entry.get("year")
            if not year:
                continue
            fin = (
                db.session.execute(
                    select(CompanyFinancial).where(
                        CompanyFinancial.ticker == ticker,
                        CompanyFinancial.year == year,
                    )
                )
                .scalars()
                .first()
            )
            if fin is None:
                fin = CompanyFinancial(ticker=ticker, year=year)
                db.session.add(fin)
            fin.revenue_mfcfa = entry.get("revenue_mfcfa")
            fin.net_income_mfcfa = entry.get("net_income_mfcfa")
            fin.net_dividend_per_share_fcfa = entry.get("net_dividend_per_share_fcfa")

    def upsert_stock_price(self, ticker, trade_date, quote, source="sikafinance"):
        if not ticker or not trade_date or not quote or quote.get("last") is None:
            return False

        trade_day = self._parse_trade_date(trade_date)
        row = (
            db.session.execute(
                select(StockPrice).where(
                    StockPrice.ticker == ticker,
                    StockPrice.trade_date == trade_day,
                )
            )
            .scalars()
            .first()
        )
        if row is None:
            row = StockPrice(ticker=ticker, trade_date=trade_day)
            db.session.add(row)

        row.open = quote.get("opening")
        row.high = quote.get("high")
        row.low = quote.get("low")
        row.close = quote.get("last")
        row.volume = quote.get("volume_shares")
        row.variation_pct = quote.get("variation_pct")
        row.source = source
        return True

    def sync_company_quote(self, company, trade_date=None):
        ticker = company.get("ticker")
        quote = company.get("market_quote") or {}
        if not ticker or quote.get("last") is None:
            return False

        trade_date = trade_date or datetime.now().strftime("%Y-%m-%d")
        self.upsert_company(company)
        self.upsert_stock_price(ticker, trade_date, quote)
        db.session.commit()
        return True

    def bulk_upsert_stock_prices(self, ticker, price_rows, source="sikafinance_historique"):
        """Importe un historique de séances (données Sikafinance historiques)."""
        if not ticker or not price_rows:
            return 0

        saved = 0
        for row in price_rows:
            quote = {
                "opening": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "last": row.get("close"),
                "volume_shares": row.get("volume"),
                "variation_pct": row.get("variation_pct"),
            }
            if quote.get("last") is None:
                continue
            if self.upsert_stock_price(ticker, row["date"], quote, source=source):
                saved += 1

        if saved:
            db.session.commit()
        return saved

    def sync_companies_quotes(self, companies, trade_date=None):
        trade_date = trade_date or datetime.now().strftime("%Y-%m-%d")
        synced = 0
        for company in companies:
            if self.sync_company_quote(company, trade_date=trade_date):
                synced += 1
        return synced

    def sync_market_indices(self, indices, trade_date=None):
        trade_date = trade_date or datetime.now().strftime("%Y-%m-%d")
        trade_day = self._parse_trade_date(trade_date)
        synced = 0
        for index in indices or []:
            name = index.get("name")
            if not name:
                continue
            row = (
                db.session.execute(
                    select(MarketIndex).where(
                        MarketIndex.name == name,
                        MarketIndex.trade_date == trade_day,
                    )
                )
                .scalars()
                .first()
            )
            if row is None:
                row = MarketIndex(name=name, trade_date=trade_day)
                db.session.add(row)
            row.opening = index.get("opening")
            row.high = index.get("high")
            row.low = index.get("low")
            row.last = index.get("last")
            row.variation_pct = index.get("variation_pct")
            synced += 1
        db.session.commit()
        return synced

    def get_stock_prices(self, ticker, days=120, start_date=None, end_date=None):
        query = select(StockPrice).where(StockPrice.ticker == ticker)
        if start_date:
            query = query.where(StockPrice.trade_date >= self._parse_trade_date(start_date))
        if end_date:
            query = query.where(StockPrice.trade_date <= self._parse_trade_date(end_date))
        query = query.order_by(StockPrice.trade_date.asc())

        rows = db.session.execute(query).scalars().all()
        if not rows:
            return pd.DataFrame()

        data = [
            {
                "date": row.trade_date.isoformat(),
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume,
                "variation_pct": row.variation_pct,
                "source": row.source,
            }
            for row in rows
        ]
        df = pd.DataFrame(data)
        if days and not df.empty:
            df = df.tail(days)
        return df

    def count_companies(self):
        return db.session.execute(select(func.count()).select_from(Company)).scalar() or 0

    def count_stock_prices(self, ticker):
        return (
            db.session.execute(
                select(func.count()).select_from(StockPrice).where(StockPrice.ticker == ticker)
            ).scalar()
            or 0
        )

    def count_all_stock_prices(self):
        return db.session.execute(select(func.count()).select_from(StockPrice)).scalar() or 0

    def get_price_date_range(self, ticker):
        row = db.session.execute(
            select(
                func.min(StockPrice.trade_date),
                func.max(StockPrice.trade_date),
            ).where(StockPrice.ticker == ticker)
        ).one()
        if not row[0]:
            return None, None
        return row[0].isoformat(), row[1].isoformat()

    def log_scrape_run(self, run_type, status, companies_count=0, prices_synced=0, error=None):
        now = datetime.now(timezone.utc)
        db.session.add(
            ScrapeRun(
                run_type=run_type,
                status=status,
                companies_count=companies_count,
                prices_synced=prices_synced,
                started_at=now,
                finished_at=now,
                error_message=error,
            )
        )
        db.session.commit()

    def save_daily_prices(self, ticker, frame):
        if frame.empty:
            return
        for _, row in frame.iterrows():
            trade_date = row.get("date") or row.get("trade_date")
            quote = {
                "opening": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "last": row.get("close"),
                "volume_shares": row.get("volume"),
            }
            self.upsert_company({"ticker": ticker, "symbol": ticker})
            self.upsert_stock_price(ticker, trade_date, quote, source="import")
        db.session.commit()

    def get_prices(self, ticker, start_date=None, end_date=None):
        return self.get_stock_prices(ticker, days=None, start_date=start_date, end_date=end_date)

    def close(self):
        db.session.remove()
