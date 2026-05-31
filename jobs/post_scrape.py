"""Actions après un scrape réussi (invalidation cache + pré-chauffage API)."""

import os


def run_post_scrape_hooks():
    """
    Invalide les caches Redis et reconstruit les payloads API lourds.
    À appeler depuis le worker scrape, pas depuis l'API publique.
    """
    if os.getenv("SKIP_POST_SCRAPE_HOOKS", "").lower() in ("1", "true", "yes"):
        print("⏭️  Post-scrape hooks ignorés (SKIP_POST_SCRAPE_HOOKS).")
        return

    try:
        from app import app, invalidate_companies_caches, warm_api_caches

        with app.app_context():
            print("🧹 Invalidation des caches API…")
            invalidate_companies_caches()

            from storage.market_calendar import is_brvm_trading_day
            from jobs.palmares_refresh import run_palmares_refresh_cycle

            if is_brvm_trading_day():
                run_palmares_refresh_cycle()

            if os.getenv("WARM_CACHE_AFTER_SCRAPE", "true").lower() in ("1", "true", "yes"):
                warm_api_caches()
            else:
                print("⏭️  Pré-chauffage cache désactivé (WARM_CACHE_AFTER_SCRAPE).")
    except Exception as exc:
        print(f"⚠️  Post-scrape hooks : {exc}")
