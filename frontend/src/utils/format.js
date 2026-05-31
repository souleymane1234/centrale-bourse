export function formatNumber(value) {
  if (value === null || value === undefined || value === '') return 'N/A';
  return Number(value).toLocaleString('fr-FR');
}

export function formatPercent(value) {
  if (value === null || value === undefined || value === '') return 'N/A';
  return `${Number(value).toLocaleString('fr-FR')}%`;
}

/** Affiche un pourcentage signé (croissance). */
export function formatGrowthPercent(value) {
  if (value === null || value === undefined || value === '') return 'N/A';
  const num = Number(value);
  const prefix = num > 0 ? '+' : '';
  return `${prefix}${num.toLocaleString('fr-FR')}%`;
}

/** Nombre de titres / grands entiers. */
export function formatShares(value) {
  if (value === null || value === undefined || value === '') return 'N/A';
  return Number(value).toLocaleString('fr-FR');
}

/** Valorisation en millions de FCFA (Sikafinance). */
export function formatMarketCapMfcfa(value) {
  if (value === null || value === undefined || value === '') return 'N/A';
  return `${Number(value).toLocaleString('fr-FR')} M FCFA`;
}

/** Montant par action (BNPA, dividende). */
export function formatPerShareFcfa(value) {
  if (value === null || value === undefined || value === '') return 'N/A';
  return `${Number(value).toLocaleString('fr-FR')} FCFA`;
}

export function formatCurrency(value, suffix = 'FCFA') {
  if (value === null || value === undefined || value === '') return 'N/A';
  return `${Number(value).toLocaleString('fr-FR')} ${suffix}`;
}

export function formatText(value) {
  return value || 'N/A';
}

export function variationClass(value) {
  if (value > 0) return 'text-emerald-600';
  if (value < 0) return 'text-rose-600';
  return 'text-slate-500';
}

export function formatDateTime(value) {
  if (!value) return 'N/A';
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function variationBadgeClass(value) {
  if (value > 0) return 'bg-emerald-100 text-emerald-800';
  if (value < 0) return 'bg-rose-100 text-rose-800';
  return 'bg-slate-100 text-slate-700';
}
