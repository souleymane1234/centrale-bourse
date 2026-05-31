"""Backend SQLite (développement local sans Docker)."""

import os
import sqlite3
from datetime import datetime, timezone

import pandas as pd

from storage.config import get_sqlite_path

DEFAULT_DB_PATH = get_sqlite_path()


class SQLiteDatabase:
    """Accès SQLite : sociétés, cours quotidiens, fondamentaux."""

    def __init__(self, db_path=None):
        self.engine = "sqlite"
        self.db_path = db_path or get_sqlite_path()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.create_tables()
        self._migrate_legacy_daily_prices()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS companies (
                ticker TEXT PRIMARY KEY,
                symbol TEXT,
                name TEXT,
                sector TEXT,
                listing_date TEXT,
                brvm_profile_url TEXT,
                sikafinance_code TEXT,
                updated_at TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stock_prices (
                ticker TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                variation_pct REAL,
                source TEXT DEFAULT 'sikafinance',
                created_at TEXT,
                PRIMARY KEY (ticker, trade_date),
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_date
            ON stock_prices (ticker, trade_date DESC)
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fundamentals (
                ticker TEXT NOT NULL,
                period_date TEXT NOT NULL,
                revenue REAL,
                net_income REAL,
                eps REAL,
                pe_ratio REAL,
                source TEXT,
                created_at TEXT,
                PRIMARY KEY (ticker, period_date)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scrape_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_type TEXT NOT NULL,
                status TEXT NOT NULL,
                companies_count INTEGER,
                prices_synced INTEGER,
                started_at TEXT,
                finished_at TEXT,
                error_message TEXT
            )
            """
        )
        self.conn.commit()

    def _migrate_legacy_daily_prices(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='daily_prices'"
        )
        if not cursor.fetchone():
            return
        cursor.execute(
            """
            INSERT OR IGNORE INTO stock_prices
                (ticker, trade_date, open, high, low, close, volume, source, created_at)
            SELECT ticker, date, open, high, low, close, volume, 'legacy', datetime('now')
            FROM daily_prices
            """
        )
        self.conn.commit()

    def _now_iso(self):
        return datetime.now(timezone.utc).isoformat()

    def upsert_company(self, company):
        ticker = company.get("ticker")
        if not ticker:
            return
        quote = company.get("market_quote") or {}
        symbol = company.get("symbol")
        if not symbol and quote.get("code"):
            symbol = quote["code"].split(".", 1)[0]
        self.conn.execute(
            """
            INSERT INTO companies (
                ticker, symbol, name, sector, listing_date,
                brvm_profile_url, sikafinance_code, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET
                symbol = excluded.symbol,
                name = excluded.name,
                sector = excluded.sector,
                listing_date = excluded.listing_date,
                brvm_profile_url = excluded.brvm_profile_url,
                sikafinance_code = excluded.sikafinance_code,
                updated_at = excluded.updated_at
            """,
            (
                ticker,
                symbol,
                company.get("display_name")
                or company.get("profile_name")
                or company.get("legal_name"),
                company.get("sector"),
                company.get("listing_date"),
                company.get("brvm_profile_url"),
                quote.get("code"),
                self._now_iso(),
            ),
        )

    def upsert_stock_price(self, ticker, trade_date, quote, source="sikafinance"):
        if not ticker or not trade_date or not quote or quote.get("last") is None:
            return False
        self.conn.execute(
            """
            INSERT INTO stock_prices (
                ticker, trade_date, open, high, low, close,
                volume, variation_pct, source, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticker, trade_date) DO UPDATE SET
                open = excluded.open,
                high = excluded.high,
                low = excluded.low,
                close = excluded.close,
                volume = excluded.volume,
                variation_pct = excluded.variation_pct,
                source = excluded.source,
                created_at = excluded.created_at
            """,
            (
                ticker,
                trade_date,
                quote.get("opening"),
                quote.get("high"),
                quote.get("low"),
                quote.get("last"),
                quote.get("volume_shares"),
                quote.get("variation_pct"),
                source,
                self._now_iso(),
            ),
        )
        return True

    def sync_company_quote(self, company, trade_date=None):
        ticker = company.get("ticker")
        quote = company.get("market_quote") or {}
        if not ticker or quote.get("last") is None:
            return False
        trade_date = trade_date or datetime.now().strftime("%Y-%m-%d")
        self.upsert_company(company)
        self.upsert_stock_price(ticker, trade_date, quote)
        self.conn.commit()
        return True

    def bulk_upsert_stock_prices(self, ticker, price_rows, source="sikafinance_historique"):
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
            if self.upsert_stock_price(ticker, row["date"], quote, source=source):
                saved += 1
        self.conn.commit()
        return saved

    def sync_companies_quotes(self, companies, trade_date=None):
        trade_date = trade_date or datetime.now().strftime("%Y-%m-%d")
        synced = 0
        for company in companies:
            if self.sync_company_quote(company, trade_date=trade_date):
                synced += 1
        return synced

    def get_stock_prices(self, ticker, days=120, start_date=None, end_date=None):
        query = """
            SELECT trade_date AS date, open, high, low, close, volume, variation_pct, source
            FROM stock_prices WHERE ticker = ?
        """
        params = [ticker]
        if start_date:
            query += " AND trade_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND trade_date <= ?"
            params.append(end_date)
        query += " ORDER BY trade_date ASC"
        df = pd.read_sql(query, self.conn, params=params)
        if days and not df.empty:
            df = df.tail(days)
        return df

    def count_companies(self):
        row = self.conn.execute("SELECT COUNT(*) AS count FROM companies").fetchone()
        return row["count"] if row else 0

    def count_stock_prices(self, ticker):
        row = self.conn.execute(
            "SELECT COUNT(*) AS count FROM stock_prices WHERE ticker = ?",
            (ticker,),
        ).fetchone()
        return row["count"] if row else 0

    def count_all_stock_prices(self):
        row = self.conn.execute("SELECT COUNT(*) AS count FROM stock_prices").fetchone()
        return row["count"] if row else 0

    def get_price_date_range(self, ticker):
        row = self.conn.execute(
            """
            SELECT MIN(trade_date) AS first_date, MAX(trade_date) AS last_date
            FROM stock_prices WHERE ticker = ?
            """,
            (ticker,),
        ).fetchone()
        if not row or not row["first_date"]:
            return None, None
        return row["first_date"], row["last_date"]

    def log_scrape_run(self, run_type, status, companies_count=0, prices_synced=0, error=None):
        now = self._now_iso()
        self.conn.execute(
            """
            INSERT INTO scrape_runs (
                run_type, status, companies_count, prices_synced,
                started_at, finished_at, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_type, status, companies_count, prices_synced, now, now, error),
        )
        self.conn.commit()

    def save_daily_prices(self, ticker, df):
        if df.empty:
            return
        rows = df.copy()
        if "date" not in rows.columns and "trade_date" in rows.columns:
            rows["date"] = rows["trade_date"]
        for _, row in rows.iterrows():
            quote = {
                "opening": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "last": row.get("close"),
                "volume_shares": row.get("volume"),
            }
            self.upsert_company({"ticker": ticker, "symbol": ticker})
            self.upsert_stock_price(ticker, row["date"], quote, source="import")
        self.conn.commit()

    def get_prices(self, ticker, start_date=None, end_date=None):
        return self.get_stock_prices(ticker, days=None, start_date=start_date, end_date=end_date)

    def close(self):
        self.conn.close()
