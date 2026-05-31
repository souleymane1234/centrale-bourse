"""Snapshot palmarès Sikafinance (Top hausses / Top baisses)."""

import json
import os
from datetime import datetime, timezone

from storage.market_calendar import brvm_now, is_brvm_trading_day

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PALMARES_SNAPSHOT_PATH = os.path.join(BASE_DIR, "data", "palmares_snapshot.json")


def load_palmares_snapshot():
    if not os.path.exists(PALMARES_SNAPSHOT_PATH):
        return None
    try:
        with open(PALMARES_SNAPSHOT_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as exc:
        print(f"⚠️  Lecture palmarès snapshot : {exc}")
        return None


def save_palmares_snapshot(payload):
    enriched = {
        **(payload or {}),
        "saved_at": brvm_now().isoformat(),
        "saved_on_trading_day": is_brvm_trading_day(),
    }
    try:
        os.makedirs(os.path.dirname(PALMARES_SNAPSHOT_PATH), exist_ok=True)
        with open(PALMARES_SNAPSHOT_PATH, "w", encoding="utf-8") as file:
            json.dump(enriched, file, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f"⚠️  Sauvegarde palmarès snapshot : {exc}")
        raise
    return enriched


def fetch_live_palmares(limit=30):
    from collectors.company_info_scraper import CompanyInfoScraper

    return CompanyInfoScraper().fetch_sikafinance_palmares_movers(limit=limit)


def refresh_palmares_snapshot(limit=30):
    """Récupère Sikafinance et persiste data/palmares_snapshot.json."""
    payload = fetch_live_palmares(limit=limit)
    return save_palmares_snapshot(payload)


def snapshot_age_hours():
    snap = load_palmares_snapshot()
    if not snap:
        return None
    raw = snap.get("fetched_at") or snap.get("saved_at")
    if not raw:
        return None
    try:
        saved = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if saved.tzinfo is None:
            saved = saved.replace(tzinfo=timezone.utc)
        delta = brvm_now() - saved.astimezone(brvm_now().tzinfo)
        return delta.total_seconds() / 3600
    except ValueError:
        return None
