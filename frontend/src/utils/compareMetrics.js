import {
  formatCurrency,
  formatGrowthPercent,
  formatMarketCapMfcfa,
  formatNumber,
  formatPercent,
  formatPerShareFcfa,
  formatShares,
  formatText,
} from './format';

export function formatMetricValue(key, value) {
  if (value === null || value === undefined || value === '') return 'N/A';

  if (key === 'price' || key === 'high_52w' || key === 'low_52w' || key === 'opening') {
    return formatCurrency(value);
  }
  if (key.includes('growth') || key.includes('perf_') || key === 'variation' || key.endsWith('_pct')) {
    if (key === 'variation') return formatPercent(value);
    return formatGrowthPercent(value);
  }
  if (key === 'market_cap_mfcfa') return formatMarketCapMfcfa(value);
  if (key === 'dividend_per_share_fcfa' || key === 'eps_fcfa') return formatPerShareFcfa(value);
  if (key === 'volume' || key === 'shares_outstanding') return formatShares(value);
  if (
    key === 'revenue_mfcfa' ||
    key === 'net_income_mfcfa' ||
    key === 'total_assets_mfcfa' ||
    key === 'equity_mfcfa' ||
    key === 'debt_mfcfa'
  ) {
    return `${formatNumber(value)} M`;
  }
  if (key === 'debt_to_equity_pct' || key === 'roe_pct' || key === 'roa_pct') {
    return formatGrowthPercent(value);
  }
  if (key === 'price_to_book') {
    return formatNumber(value);
  }
  if (key === 'investor_score') return `${formatNumber(value)}/100`;
  return formatNumber(value);
}

export function recommendationLabel(code) {
  if (code === 'attractive') return { label: 'Attractive', className: 'bg-emerald-100 text-emerald-800' };
  if (code === 'watch') return { label: 'À surveiller', className: 'bg-rose-100 text-rose-800' };
  return { label: 'Neutre', className: 'bg-amber-100 text-amber-800' };
}

export const RANKING_LABELS = {
  dividend_yield: 'Meilleur rendement dividende',
  growth_revenue_5y: 'Meilleure croissance CA (CAGR 5 ans)',
  profitability_margin: 'Meilleure marge nette',
  market_performance_1y: 'Meilleure perf. 1 an',
  valuation_pe: 'PER le plus bas',
  market_variation_day: 'Meilleure variation du jour',
};
