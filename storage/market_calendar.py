"""
Calendrier boursier BRVM : pas de séance le samedi ni le dimanche.
Horaires de séance continue (heure d'Abidjan) : 9h30 – 15h30 par défaut.
"""
import os
from datetime import datetime, time, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

BRVM_TIMEZONE = "Africa/Abidjan"
WEEKDAY_LABELS = {
    0: "lundi",
    1: "mardi",
    2: "mercredi",
    3: "jeudi",
    4: "vendredi",
    5: "samedi",
    6: "dimanche",
}


def _market_open_time():
    return time(
        int(os.getenv("BRVM_OPEN_HOUR", "9")),
        int(os.getenv("BRVM_OPEN_MINUTE", "30")),
    )


def _market_close_time():
    return time(
        int(os.getenv("BRVM_CLOSE_HOUR", "15")),
        int(os.getenv("BRVM_CLOSE_MINUTE", "30")),
    )


def brvm_now():
    """Date/heure courante au fuseau de la BRVM (Abidjan)."""
    if ZoneInfo is not None:
        return datetime.now(ZoneInfo(BRVM_TIMEZONE))
    return datetime.now()


def is_brvm_trading_day(dt=None):
    """True du lundi au vendredi (jour de bourse)."""
    moment = dt or brvm_now()
    return moment.weekday() < 5


def _session_bounds(moment):
    open_t = _market_open_time()
    close_t = _market_close_time()
    session_open = moment.replace(
        hour=open_t.hour,
        minute=open_t.minute,
        second=0,
        microsecond=0,
    )
    session_close = moment.replace(
        hour=close_t.hour,
        minute=close_t.minute,
        second=0,
        microsecond=0,
    )
    return session_open, session_close


def _format_time(moment):
    return moment.strftime("%Hh%M")


def _next_trading_day_start(moment):
    candidate = moment
    for _ in range(8):
        if is_brvm_trading_day(candidate):
            session_open, _ = _session_bounds(candidate)
            if candidate.date() == moment.date():
                if moment < session_open:
                    return session_open
            elif candidate.date() > moment.date():
                return session_open
        candidate = (candidate + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    return None


def get_brvm_market_status(dt=None):
    """État ouvert / fermé de la séance BRVM pour l'interface."""
    moment = dt or brvm_now()
    session_open, session_close = _session_bounds(moment)
    trading_day = is_brvm_trading_day(moment)
    open_label = _format_time(session_open)
    close_label = _format_time(session_close)

    base = {
        "timezone": BRVM_TIMEZONE,
        "local_time": moment.isoformat(),
        "session_open": open_label,
        "session_close": close_label,
        "is_trading_day": trading_day,
    }

    if not trading_day:
        next_open = _next_trading_day_start(moment)
        detail = (
            f"Prochaine séance : {WEEKDAY_LABELS[next_open.weekday()]} à {_format_time(next_open)}."
            if next_open
            else f"Séance du lundi au vendredi, {open_label} – {close_label} (Abidjan)."
        )
        return {
            **base,
            "is_open": False,
            "status": "weekend",
            "label": "Marché fermé",
            "detail": detail,
        }

    if moment < session_open:
        return {
            **base,
            "is_open": False,
            "status": "before_open",
            "label": "Marché fermé",
            "detail": f"Ouverture à {open_label} (heure d'Abidjan).",
        }

    if moment >= session_close:
        next_open = _next_trading_day_start(moment)
        detail = (
            f"Séance terminée. Prochaine ouverture : {WEEKDAY_LABELS[next_open.weekday()]} à {_format_time(next_open)}."
            if next_open
            else f"Séance terminée à {close_label}."
        )
        return {
            **base,
            "is_open": False,
            "status": "after_close",
            "label": "Marché fermé",
            "detail": detail,
        }

    return {
        **base,
        "is_open": True,
        "status": "open",
        "label": "Marché ouvert",
        "detail": f"Séance en cours jusqu'à {close_label} (heure d'Abidjan).",
    }


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
