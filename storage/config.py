import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# .env prioritaire ; .env.example en secours si .env vide ou absent
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env.example"), override=False)


def get_db_engine():
    return os.getenv("DB_ENGINE", "sqlite").strip().lower()


def get_sqlite_path():
    default = os.path.join(BASE_DIR, "data", "brvm.db")
    return os.getenv("DATABASE_PATH", default)


def get_mysql_url():
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit

    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    user = quote_plus(os.getenv("MYSQL_USER", "brvm"))
    password = quote_plus(os.getenv("MYSQL_PASSWORD", "brvm_secret"))
    database = os.getenv("MYSQL_DATABASE", "brvm_agent")

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
