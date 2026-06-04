const WEEKDAY_SHORT = { lun: 1, mar: 2, mer: 3, jeu: 4, ven: 5, sam: 6, dim: 0 };

function getAbidjanParts(now = new Date()) {
  const formatter = new Intl.DateTimeFormat('fr-FR', {
    timeZone: 'Africa/Abidjan',
    weekday: 'short',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
  const parts = formatter.formatToParts(now);
  const get = (type) => parts.find((part) => part.type === type)?.value || '';
  const weekdayKey = get('weekday').replace('.', '').toLowerCase();
  return {
    weekday: WEEKDAY_SHORT[weekdayKey] ?? now.getDay(),
    hour: Number(get('hour')),
    minute: Number(get('minute')),
  };
}

/** Repli client si l'API n'a pas encore market_status (cache ancien). */
export function getBrvmMarketStatusFallback() {
  const { weekday, hour, minute } = getAbidjanParts();
  const sessionOpen = '9h30';
  const sessionClose = '15h30';
  const openMinutes = 9 * 60 + 30;
  const closeMinutes = 15 * 60 + 30;
  const nowMinutes = hour * 60 + minute;
  const tradingDay = weekday >= 1 && weekday <= 5;

  if (!tradingDay) {
    return {
      is_open: false,
      label: 'Marché fermé',
      detail: 'Séance du lundi au vendredi, 9h30 – 15h30 (Abidjan).',
      session_open: sessionOpen,
      session_close: sessionClose,
    };
  }

  if (nowMinutes < openMinutes) {
    return {
      is_open: false,
      label: 'Marché fermé',
      detail: `Ouverture à ${sessionOpen} (heure d'Abidjan).`,
      session_open: sessionOpen,
      session_close: sessionClose,
    };
  }

  if (nowMinutes >= closeMinutes) {
    return {
      is_open: false,
      label: 'Marché fermé',
      detail: `Séance terminée à ${sessionClose}.`,
      session_open: sessionOpen,
      session_close: sessionClose,
    };
  }

  return {
    is_open: true,
    label: 'Marché ouvert',
    detail: `Séance en cours jusqu'à ${sessionClose} (heure d'Abidjan).`,
    session_open: sessionOpen,
    session_close: sessionClose,
  };
}
