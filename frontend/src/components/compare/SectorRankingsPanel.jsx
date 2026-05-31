import { Link } from 'react-router-dom';
import { companyPath } from '../../utils/routing';
import { formatMetricValue, RANKING_LABELS } from '../../utils/compareMetrics';
import { formatText } from '../../utils/format';

const METRIC_KEY_MAP = {
  dividend_yield: 'dividend_yield_pct',
  growth_revenue_5y: 'revenue_growth_5y_pct',
  profitability_margin: 'net_margin_pct',
  market_performance_1y: 'perf_1y_pct',
  valuation_pe: 'pe_ratio',
  market_variation_day: 'variation',
};

export default function SectorRankingsPanel({ rankings }) {
  if (!rankings) return null;

  return (
    <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {Object.entries(RANKING_LABELS).map(([key, title]) => {
        const rows = rankings[key];
        const metricKey = METRIC_KEY_MAP[key];
        if (!rows?.length) return null;

        return (
          <div key={key} className="rounded-xl border border-slate-200 bg-slate-50/80 p-3">
            <h4 className="text-xs font-bold uppercase tracking-wide text-slate-500">{title}</h4>
            <ol className="mt-2 space-y-1.5">
              {rows.slice(0, 5).map((row) => (
                <li key={row.ticker} className="flex items-center justify-between gap-2 text-sm">
                  <span className="flex items-center gap-2 min-w-0">
                    <span className="font-bold text-brand-700">{row.rank}.</span>
                    <Link
                      to={companyPath(row.ticker)}
                      className="truncate font-medium text-slate-900 hover:underline"
                    >
                      {formatText(row.symbol || row.ticker)}
                    </Link>
                  </span>
                  <span className="shrink-0 font-semibold text-slate-700">
                    {formatMetricValue(metricKey, row.value)}
                  </span>
                </li>
              ))}
            </ol>
          </div>
        );
      })}
    </div>
  );
}
