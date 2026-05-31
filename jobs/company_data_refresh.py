"""Scraping périodique du dataset sociétés (BRVM + Sikafinance)."""

import os
import threading
import time

from collectors.company_info_scraper import CompanyInfoScraper
from storage.app_factory import create_app
from storage.database import create_database
from storage.market_calendar import is_brvm_trading_day, weekend_skip_message
from storage.price_sync import backfill_from_companies_payload

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUTPUT_PATH = os.path.join(BASE_DIR, "data", "companies_full.json")

_scrape_lock = threading.Lock()
_scheduler_started = False
_scheduler_lock = threading.Lock()
_last_scrape_status = {
    "running": False,
    "last_success_at": None,
    "last_error": None,
    "last_companies_count": None,
}


def get_scrape_status():
    """État du dernier scrape planifié (lecture seule)."""
    status = dict(_last_scrape_status)
    status["market_open"] = is_brvm_trading_day()
    if not status["market_open"]:
        status["skip_reason"] = weekend_skip_message()
    return status


def refresh_companies_dataset(output_path=None):
    """Lance le scrape complet et écrit companies_full.json."""
    output_path = output_path or DEFAULT_OUTPUT_PATH
    scraper = CompanyInfoScraper()
    payload = scraper.scrape_all_company_data()
    scraper.save_to_json(payload, output_path)
    return payload


def run_scrape_cycle(on_complete=None, *, force=False):
    """
    Un cycle complet : scrape JSON, sync MySQL, callback optionnel.
    Retourne True si succès.
    """
    return _run_scrape_cycle(on_complete=on_complete, force=force)


def _run_scrape_cycle(on_complete=None, *, force=False):
    global _last_scrape_status

    if not force and not is_brvm_trading_day():
        print(f"⏸️  {weekend_skip_message()}")
        return False

    if not _scrape_lock.acquire(blocking=False):
        print("⏭️  Scrape sociétés déjà en cours, cycle ignoré.")
        return False

    _last_scrape_status["running"] = True
    _last_scrape_status["last_error"] = None

    try:
        print("🔄 Démarrage du scrape sociétés (BRVM + Sikafinance)...")
        payload = refresh_companies_dataset()
        _last_scrape_status["last_success_at"] = payload.get("generated_at")
        _last_scrape_status["last_companies_count"] = payload.get("companies_count")
        print(
            f"✅ Scrape terminé : {payload.get('companies_count')} sociétés "
            f"({payload.get('generated_at')})"
        )
        try:
            flask_app = create_app()
            with flask_app.app_context():
                database = create_database()
                prices_synced, listed_count = backfill_from_companies_payload(
                    payload, db=database
                )
                companies_in_db = database.count_companies()
                database.log_scrape_run(
                    "companies_full",
                    "success",
                    companies_count=listed_count,
                    prices_synced=prices_synced,
                )
                print(
                    f"💾 {listed_count} sociétés cotées → {companies_in_db} en base "
                    f"({prices_synced} cours du jour) — {database.db_path}"
                )
        except Exception as sync_exc:
            print(f"⚠️  Sync base cours : {sync_exc}")
        if on_complete:
            on_complete()
        return True
    except Exception as exc:
        _last_scrape_status["last_error"] = str(exc)
        print(f"❌ Erreur lors du scrape sociétés : {exc}")
        return False
    finally:
        _last_scrape_status["running"] = False
        _scrape_lock.release()


def run_scrape_worker_forever(on_complete=None):
    """Boucle scrape (processus worker dédié, pas l'API Flask)."""
    _scrape_worker(on_complete=on_complete)


def _scrape_worker(on_complete=None):
    interval_hours = float(os.getenv("SCRAPE_INTERVAL_HOURS", "2"))
    interval_seconds = max(300, int(interval_hours * 3600))
    run_immediately = os.getenv("SCRAPE_ON_STARTUP", "true").lower() not in (
        "0",
        "false",
        "no",
    )

    print(
        f"📅 Planificateur scrape actif : toutes les {interval_hours:g} h "
        f"({interval_seconds} s), hors samedi/dimanche (BRVM fermée)"
    )

    while True:
        if run_immediately:
            if is_brvm_trading_day():
                _run_scrape_cycle(on_complete)
            else:
                print(f"⏸️  {weekend_skip_message()}")
        run_immediately = True
        time.sleep(interval_seconds)


def start_scrape_scheduler(on_complete=None):
    """Démarre le thread de scrape périodique (une seule instance par processus)."""
    global _scheduler_started

    if os.getenv("DISABLE_SCRAPE_SCHEDULER", "").lower() in ("1", "true", "yes"):
        print("⏸️  Planificateur scrape désactivé (DISABLE_SCRAPE_SCHEDULER).")
        return

    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True

    thread = threading.Thread(
        target=_scrape_worker,
        kwargs={"on_complete": on_complete},
        name="company-scrape-scheduler",
        daemon=True,
    )
    thread.start()
