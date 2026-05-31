/** Configuration des KPI pour le tableau comparatif par secteur. */

export const COMPARE_MATRIX_SECTIONS = [
  {
    id: 'size',
    title: 'Taille & volume',
    icon: '⚓',
    rows: [
      { key: 'market_cap_mfcfa', label: 'Cap. (Mds FCFA)', format: 'billions', higherBetter: true },
      { key: 'revenue_mfcfa', label: 'CA (Mds FCFA, 12MG)', format: 'billions', higherBetter: true },
      { key: 'net_income_mfcfa', label: 'RN (Mds FCFA, 12MG)', format: 'billions', higherBetter: true },
    ],
  },
  {
    id: 'growth',
    title: 'Croissance & momentum',
    icon: '🚀',
    rows: [
      { key: 'revenue_growth_pct', label: 'Croiss. CA (%, dernier ex.)', format: 'percentSigned', higherBetter: true },
      { key: 'revenue_growth_5y_pct', label: 'CAGR CA (%, 5 ans)', format: 'percentSigned', higherBetter: true },
      { key: 'net_income_growth_pct', label: 'Croiss. RN (%, dernier ex.)', format: 'percentSigned', higherBetter: true },
      { key: 'net_income_growth_5y_pct', label: 'CAGR RN (%, 5 ans)', format: 'percentSigned', higherBetter: true },
      { key: 'perf_1y_pct', label: 'Perf. cours (%, 1 an)', format: 'percentSigned', higherBetter: true },
    ],
  },
  {
    id: 'profitability',
    title: 'Efficacité et rentabilité',
    icon: '🏆',
    rows: [
      { key: 'net_margin_pct', label: 'Marge N. (%, 12MG)', format: 'percent', higherBetter: true },
      { key: 'roe_pct', label: 'ROE (%, 12MG)', format: 'percent', higherBetter: true },
      { key: 'roa_pct', label: 'ROA (%, 12MG)', format: 'percent', higherBetter: true },
    ],
  },
  {
    id: 'valuation',
    title: 'Valorisation',
    icon: '💎',
    rows: [
      { key: 'pe_ratio', label: 'PER (12MG)', format: 'ratio', higherBetter: false },
      { key: 'price_to_book', label: 'PBR (12MG)', format: 'ratio', higherBetter: false },
      { key: 'psr', label: 'PSR (12MG)', format: 'ratio', higherBetter: false },
    ],
  },
  {
    id: 'yield',
    title: 'Rendement',
    icon: '🪙',
    rows: [
      { key: 'dividend_per_share_fcfa', label: 'Dernier div. (FCFA)', format: 'perShare', higherBetter: true },
      { key: 'dividend_yield_pct', label: 'Rendement (%)', format: 'percent', higherBetter: true },
      { key: 'payout_ratio_pct', label: 'Taux de distribution (%)', format: 'percent', higherBetter: null },
    ],
  },
];

export function getMatrixCellValue(company, rowKey) {
  if (rowKey === 'psr') {
    const cap = company.market_cap_mfcfa;
    const revenue = company.revenue_mfcfa;
    if (cap == null || revenue == null || revenue === 0) return null;
    return Math.round((cap / revenue) * 100) / 100;
  }
  return company[rowKey];
}

export function formatMatrixValue(value, format) {
  if (value === null || value === undefined || value === '') return '—';

  const num = Number(value);
  if (Number.isNaN(num)) return '—';

  if (format === 'billions') {
    const billions = num / 1000;
    return billions.toLocaleString('fr-FR', { maximumFractionDigits: 1, minimumFractionDigits: 0 });
  }
  if (format === 'percentSigned') {
    const prefix = num > 0 ? '+' : '';
    return `${prefix}${num.toLocaleString('fr-FR', { maximumFractionDigits: 2 })} %`;
  }
  if (format === 'percent') {
    return `${num.toLocaleString('fr-FR', { maximumFractionDigits: 2 })} %`;
  }
  if (format === 'perShare') {
    return `${num.toLocaleString('fr-FR', { maximumFractionDigits: 0 })}`;
  }
  if (format === 'ratio') {
    return num.toLocaleString('fr-FR', { maximumFractionDigits: 2 });
  }
  return String(value);
}

export function cellTone(value, format, higherBetter) {
  if (value === null || value === undefined || value === '' || higherBetter == null) {
    return 'neutral';
  }
  const num = Number(value);
  if (Number.isNaN(num)) return 'neutral';

  if (format === 'percentSigned') {
    if (num > 0) return 'positive';
    if (num < 0) return 'negative';
    return 'neutral';
  }

  return 'neutral';
}

/** Meilleure / plus faible valeur dans la ligne (couleur texte uniquement). */
export function peerRankTone(value, peersValues, higherBetter) {
  if (value == null || value === '' || higherBetter == null) return 'neutral';

  const nums = peersValues
    .map((item) => (item == null || item === '' ? null : Number(item)))
    .filter((item) => item !== null && !Number.isNaN(item));

  if (nums.length < 2) return 'neutral';

  const num = Number(value);
  if (Number.isNaN(num)) return 'neutral';

  const min = Math.min(...nums);
  const max = Math.max(...nums);
  if (min === max) return 'neutral';

  const isBest = higherBetter ? num === max : num === min;
  const isWorst = higherBetter ? num === min : num === max;

  if (isBest) return 'best';
  if (isWorst) return 'worst';
  return 'neutral';
}

/** Gagnant sur une ligne (2 sociétés uniquement). */
export function pickRowWinner(companies, row) {
  if (!companies || companies.length !== 2 || row.higherBetter == null) return null;

  const [left, right] = companies;
  const leftVal = getMatrixCellValue(left, row.key);
  const rightVal = getMatrixCellValue(right, row.key);

  if (leftVal == null || rightVal == null || Number(leftVal) === Number(rightVal)) {
    return null;
  }

  const higher = row.higherBetter;
  if (higher) {
    return Number(leftVal) > Number(rightVal) ? left.ticker : right.ticker;
  }
  return Number(leftVal) < Number(rightVal) ? left.ticker : right.ticker;
}

export function countHeadToHeadWins(companies) {
  if (!companies || companies.length !== 2) {
    return { leftWins: 0, rightWins: 0 };
  }

  const [left, right] = companies;
  let leftWins = 0;
  let rightWins = 0;

  for (const section of COMPARE_MATRIX_SECTIONS) {
    for (const row of section.rows) {
      const winner = pickRowWinner(companies, row);
      if (winner === left.ticker) leftWins += 1;
      else if (winner === right.ticker) rightWins += 1;
    }
  }

  return { leftWins, rightWins };
}
