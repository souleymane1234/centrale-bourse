"""Fabrique de connexion : SQLite (local) ou MySQL (Docker)."""

from storage.config import get_db_engine, get_mysql_url, get_sqlite_path


def get_database_uri():
    if get_db_engine() == "mysql":
        return get_mysql_url()
    return f"sqlite:///{get_sqlite_path()}"


def create_database():
    if get_db_engine() == "mysql":
        from storage.mysql_database import MySQLDatabase

        return MySQLDatabase()
    from storage.sqlite_database import SQLiteDatabase

    return SQLiteDatabase()


# Alias rétrocompatible
Database = create_database
