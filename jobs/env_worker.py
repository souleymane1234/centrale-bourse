"""Variables d'environnement pour les scripts worker (scrape / warm)."""

import os


def apply_worker_env():
    """
    Le .env est calé pour l'API (ALLOW_LIVE_QUOTE_FETCH=false).
    Les scripts worker réactivent Sikafinance pour ce processus uniquement.
    """
    os.environ["ALLOW_LIVE_QUOTE_FETCH"] = "true"
    os.environ.setdefault("WARM_CACHE_AFTER_SCRAPE", "true")
    os.environ.setdefault("SCRAPE_BALANCE_SHEETS", "true")
    os.environ.setdefault("SCRAPE_ON_STARTUP", "true")
