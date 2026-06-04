-- Schéma MySQL Centrale Bourse (référence — les tables sont créées via SQLAlchemy)
-- mysql -u brvm -p brvm_agent < storage/schema.sql

CREATE TABLE IF NOT EXISTS companies (
    ticker VARCHAR(32) PRIMARY KEY,
    symbol VARCHAR(32),
    name VARCHAR(255),
    legal_name VARCHAR(255),
    sector VARCHAR(128),
    listing_date VARCHAR(64),
    brvm_profile_url VARCHAR(512),
    sikafinance_code VARCHAR(32),
    website VARCHAR(512),
    address TEXT,
    email VARCHAR(255),
    phone VARCHAR(64),
    profile_summary TEXT,
    raw_payload JSON,
    created_at DATETIME(6),
    updated_at DATETIME(6)
);

CREATE TABLE IF NOT EXISTS stock_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(32) NOT NULL,
    trade_date DATE NOT NULL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume INT,
    variation_pct DOUBLE,
    source VARCHAR(64),
    created_at DATETIME(6),
    UNIQUE KEY uq_stock_prices_ticker_date (ticker, trade_date),
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(32),
    role VARCHAR(32) DEFAULT 'user',
    is_active TINYINT(1) DEFAULT 1,
    email_verified TINYINT(1) DEFAULT 0,
    created_at DATETIME(6),
    updated_at DATETIME(6)
);

CREATE TABLE IF NOT EXISTS subscription_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(32) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    price_fcfa INT DEFAULT 0,
    billing_period VARCHAR(16) DEFAULT 'monthly',
    duration_days INT DEFAULT 30,
    features JSON,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME(6)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    plan_id INT NOT NULL,
    status VARCHAR(32) DEFAULT 'active',
    started_at DATETIME(6),
    expires_at DATETIME(6),
    cancelled_at DATETIME(6),
    auto_renew TINYINT(1) DEFAULT 1,
    external_reference VARCHAR(128),
    created_at DATETIME(6),
    updated_at DATETIME(6),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(id)
);

CREATE TABLE IF NOT EXISTS news_articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(160) NOT NULL UNIQUE,
    title VARCHAR(512) NOT NULL,
    excerpt TEXT,
    body TEXT,
    body_html TEXT,
    badge VARCHAR(32) DEFAULT 'brvm',
    media_type VARCHAR(16),
    image_url VARCHAR(1024),
    video_url VARCHAR(1024),
    thumbnail_url VARCHAR(1024),
    source VARCHAR(128),
    source_url VARCHAR(1024),
    published_at DATETIME(6),
    ticker VARCHAR(32),
    author VARCHAR(255),
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME(6),
    updated_at DATETIME(6),
    KEY ix_news_articles_badge (badge),
    KEY ix_news_articles_published_at (published_at),
    KEY ix_news_articles_ticker (ticker),
    KEY ix_news_articles_is_active (is_active)
);
