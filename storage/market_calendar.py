"""
Calendrier boursier BRVM : pas de séance le samedi ni le dimanche.
"""
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

BRVM_TIMEZONE = "Africa/Abidjan"


def brvm_now():
    """Date/heure courante au fuseau de la BRVM (Abidjan)."""
    if ZoneInfo is not None:
        return datetime.now(ZoneInfo(BRVM_TIMEZONE))
    return datetime.now()


def is_brvm_trading_day(dt=None):
    """True du lundi au vendredi (marché ouvert)."""
    moment = dt or brvm_now()
    return moment.weekday() < 5


def weekend_skip_message(dt=None):
    """Message affiché lorsque le scrape est ignoré le week-end."""
    moment = dt or brvm_now()
    day_names = {
        5: "samedi",
        6: "dimanche",
    }
    label = day_names.get(moment.weekday(), "week-end")
    return f"Marché BRVM fermé ({label}), scrape ignoré."


def weekend_palmares_message(dt=None):
    """Message lorsque le palmarès n'est pas rafraîchi le week-end."""
    moment = dt or brvm_now()
    day_names = {5: "samedi", 6: "dimanche"}
    label = day_names.get(moment.weekday(), "week-end")
    return (
        f"Marché BRVM fermé ({label}) : palmarès non mis à jour, "
        "dernière sauvegarde du vendredi utilisée."
    )
