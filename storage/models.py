"""Modèles SQLAlchemy — marché BRVM, utilisateurs, abonnements."""

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc)


class Company(db.Model):
    __tablename__ = "companies"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    symbol: Mapped[str | None] = mapped_column(String(32))
    name: Mapped[str | None] = mapped_column(String(255))
    legal_name: Mapped[str | None] = mapped_column(String(255))
    sector: Mapped[str | None] = mapped_column(String(128))
    listing_date: Mapped[str | None] = mapped_column(String(64))
    brvm_profile_url: Mapped[str | None] = mapped_column(String(512))
    sikafinance_code: Mapped[str | None] = mapped_column(String(32))
    website: Mapped[str | None] = mapped_column(String(512))
    address: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(64))
    profile_summary: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    prices: Mapped[list["StockPrice"]] = relationship(back_populates="company")
    financials: Mapped[list["CompanyFinancial"]] = relationship(back_populates="company")


class StockPrice(db.Model):
    __tablename__ = "stock_prices"
    __table_args__ = (UniqueConstraint("ticker", "trade_date", name="uq_stock_prices_ticker_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(32), ForeignKey("companies.ticker"), index=True)
    trade_date: Mapped[Date] = mapped_column(Date, index=True)
    open: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    close: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[int | None] = mapped_column(Integer)
    variation_pct: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(64), default="sikafinance")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    company: Mapped["Company"] = relationship(back_populates="prices")


class CompanyFinancial(db.Model):
    __tablename__ = "company_financials"
    __table_args__ = (UniqueConstraint("ticker", "year", name="uq_company_financials_ticker_year"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(32), ForeignKey("companies.ticker"), index=True)
    year: Mapped[int] = mapped_column(Integer)
    revenue_mfcfa: Mapped[float | None] = mapped_column(Float)
    net_income_mfcfa: Mapped[float | None] = mapped_column(Float)
    net_dividend_per_share_fcfa: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(64), default="brvm")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    company: Mapped["Company"] = relationship(back_populates="financials")


class MarketIndex(db.Model):
    __tablename__ = "market_indices"
    __table_args__ = (UniqueConstraint("name", "trade_date", name="uq_market_indices_name_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    trade_date: Mapped[Date] = mapped_column(Date, index=True)
    opening: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    last: Mapped[float | None] = mapped_column(Float)
    variation_pct: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(64), default="sikafinance")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Fundamental(db.Model):
    __tablename__ = "fundamentals"
    __table_args__ = (UniqueConstraint("ticker", "period_date", name="uq_fundamentals_ticker_period"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(32), ForeignKey("companies.ticker"), index=True)
    period_date: Mapped[str] = mapped_column(String(32))
    revenue: Mapped[float | None] = mapped_column(Float)
    net_income: Mapped[float | None] = mapped_column(Float)
    eps: Mapped[float | None] = mapped_column(Float)
    pe_ratio: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ScrapeRun(db.Model):
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    companies_count: Mapped[int | None] = mapped_column(Integer)
    prices_synced: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(32), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    referral_code: Mapped[str | None] = mapped_column(String(16), unique=True, index=True)
    referred_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    referral_balance_fcfa: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user")
    referred_by: Mapped["User | None"] = relationship(
        "User", remote_side="User.id", foreign_keys=[referred_by_user_id]
    )
    referral_earnings: Mapped[list["ReferralEarning"]] = relationship(
        back_populates="referrer", foreign_keys="ReferralEarning.referrer_user_id"
    )
    watchlist_items: Mapped[list["UserWatchlistItem"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    price_alerts: Mapped[list["UserPriceAlert"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserSession(db.Model):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="sessions")


class SubscriptionPlan(db.Model):
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    price_fcfa: Mapped[int] = mapped_column(Integer, default=0)
    billing_period: Mapped[str] = mapped_column(String(16), default="monthly")
    duration_days: Mapped[int] = mapped_column(Integer, default=30)
    features: Mapped[dict | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscription_plans.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
    external_reference: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    user: Mapped["User"] = relationship(back_populates="subscriptions")
    plan: Mapped["SubscriptionPlan"] = relationship(back_populates="subscriptions")


class ReferralEarning(db.Model):
    __tablename__ = "referral_earnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    referrer_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    referred_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    subscription_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("subscriptions.id"))
    payment_fcfa: Mapped[int] = mapped_column(Integer, default=0)
    commission_fcfa: Mapped[int] = mapped_column(Integer, default=0)
    commission_rate: Mapped[float] = mapped_column(Float, default=0.20)
    kind: Mapped[str] = mapped_column(String(32), default="subscription")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    referrer: Mapped["User"] = relationship(
        back_populates="referral_earnings", foreign_keys=[referrer_user_id]
    )


class UserWatchlistItem(db.Model):
    __tablename__ = "user_watchlist"
    __table_args__ = (db.UniqueConstraint("user_id", "ticker", name="uq_user_watchlist_ticker"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="watchlist_items")


class UserPriceAlert(db.Model):
    __tablename__ = "user_price_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(32), index=True)
    direction: Mapped[str] = mapped_column(String(8))  # above | below
    target_price: Mapped[float] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    user: Mapped["User"] = relationship(back_populates="price_alerts")
