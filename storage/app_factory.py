"""Application Flask et configuration base de données."""

import os

from flask import Flask

from storage.config import get_db_engine
from storage.database import get_database_uri
from storage.models import db


def configure_app(app):
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "brvm-dashboard-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }
    db.init_app(app)
    return app


def create_app():
    app = Flask(__name__, static_folder=None)
    configure_app(app)
    return app
