"""
Rafraîchissement automatique du palmarès Sikafinance (Top hausses / baisses).

- Lundi–vendredi : toutes les 4 h (fuseau Abidjan / BRVM)
- Samedi–dimanche : aucun fetch — conservation du dernier snapshot (vendredi)
"""

import os
import threading
import time

from jobs.env_worker import apply_worker_env
from storage.market_calendar import is_brvm_trading_day, weekend_palmares_message
from storage.palmares_store import load_palmares_snapshot, refresh_palmares_snapshot

_palmares_lock = threading.Lock()
_scheduler_started = False
_scheduler_lock = threading.Lock()
_last_status = {
    "running": False,
    "last_success_at": None,
    "last_error": None,
    "gainers_count": None,
    "losers_count": None,
    "source": "sikafinance_palmares",
}


def get_palmares_refresh_status():
    status = dict(_last_status)
    status["market_open"] = is_brvm_trading_day()
    status["snapshot"] = _snapshot_meta()
    if not status["market_open"]:
        status["skip_reason"] = weekend_palmares_message()
    return status


def _snapshot_meta():
    snap = load_palmares_snapshot()
    if not snap:
        return None
    return {
        "saved_at": snap.get("saved_at") or snap.get("fetched_at"),
        "saved_on_trading_day": snap.get("saved_on_trading_day"),
        "gainers_count": len(snap.get("gainers") or []),
        "losers_count": len(snap.get("losers") or []),
        "source_url": snap.get("source_url"),
    }


def _invalidate_palmares_api_caches():
    from app import (
        CACHE_KEY_HOME,
        CACHE_KEY_MARKET_SUMMARY,
        CACHE_KEY_PALMARES,
        build_market_summary,
        invalidate_companies_caches,
    )

    invalidate_companies_caches()
    build_market_summary()


def run_palmares_refresh_cycle(*, force=False):
    """
    Un cycle : fetch Sikafinance + snapshot + invalidation cache API.
    Retourne True si un nouveau snapshot a été écrit.
    """
    global _last_status

    if not force and not is_brvm_trading_day():
        snap = load_palmares_snapshot()
        print(f"⏸️  {weekend_palmares_message()}")
        if snap:
            saved = snap.get("saved_at") or snap.get("fetched_at")
            print(f"   Dernier palmarès conservé : {saved}")
        return False

    if not _palmares_lock.acquire(blocking=False):
        print("⏭️  Rafraîchissement palmarès déjà en cours, cycle ignoré.")
        return False

    _last_status["running"] = True
    _last_status["last_error"] = None

    try:
        apply_worker_env()
        os.environ["ALLOW_LIVE_QUOTE_FETCH"] = "true"
        print("📈 Rafraîchissement palmarès Sikafinance (Variation hausses/baisses)…")
        payload = refresh_palmares_snapshot(limit=int(os.getenv("PALMARES_FETCH_LIMIT", "30")))
        _last_status["last_success_at"] = payload.get("saved_at") or payload.get("fetched_at")
        _last_status["gainers_count"] = len(payload.get("gainers") or [])
        _last_status["losers_count"] = len(payload.get("losers") or [])

        from app import app

        with app.app_context():
            _invalidate_palmares_api_caches()

        print(
            f"✅ Palmarès à jour : {_last_status['gainers_count']} hausses, "
            f"{_last_status['losers_count']} baisses"
        )
        return True
    except Exception as exc:
        _last_status["last_error"] = str(exc)
        print(f"❌ Erreur palmarès : {exc}")
        return False
    finally:
        _last_status["running"] = False
        _palmares_lock.release()


def palmares_scheduler_disabled():
    return os.getenv("DISABLE_PALMARES_SCHEDULER", "").lower() in ("1", "true", "yes")


def _palmares_worker():
    interval_hours = float(os.getenv("PALMARES_INTERVAL_HOURS", "4"))
    interval_seconds = max(600, int(interval_hours * 3600))
    run_immediately = os.getenv("PALMARES_ON_STARTUP", "true").lower() not in (
        "0",
        "false",
        "no",
    )

    print(
        f"📅 Planificateur palmarès : toutes les {interval_hours:g} h (lun–ven), "
        f"week-end = dernier snapshot du vendredi"
    )

    while True:
        if run_immediately:
            run_palmares_refresh_cycle()
        run_immediately = True
        time.sleep(interval_seconds)


def start_palmares_scheduler():
    global _scheduler_started

    if palmares_scheduler_disabled():
        print("⏸️  Planificateur palmarès désactivé (DISABLE_PALMARES_SCHEDULER).")
        return

    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True

    thread = threading.Thread(
        target=_palmares_worker,
        name="palmares-refresh-scheduler",
        daemon=True,
    )
    thread.start()
