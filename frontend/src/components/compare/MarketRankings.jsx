import { useEffect, useMemo, useState } from 'react';
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

function RankingList({ title, rows, metricKey }) {
  if (!rows?.length) {
    return (
      <article className="rounded-xl border border-slate-200 bg-slate-50/50 p-4">
        <h3 className="text-sm font-bold text-slate-900">{title}</h3>
        <p className="mt-2 text-xs text-slate-500">Données insuffisantes pour ce classement.</p>
      </article>
    );
  }

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4">
      <h3 className="text-sm font-bold text-slate-900">{title}</h3>
      <ol className="mt-3 space-y-2">
        {rows.slice(0, 8).map((row) => (
          <li key={`${title}-${row.ticker}`} className="flex items-center justify-between gap-2 text-sm">
            <div className="flex min-w-0 items-center gap-2">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-50 text-xs font-bold text-brand-800">
                {row.rank}
              </span>
              <Link
                to={companyPath(row.ticker)}
                className="truncate font-semibold text-slate-900 hover:text-brand-700"
              >
                {formatText(row.symbol || row.ticker)}
              </Link>
            </div>
            <span className="shrink-0 font-semibold text-slate-800">
              {formatMetricValue(metricKey, row.value)}
            </span>
          </li>
        ))}
      </ol>
    </article>
  );
}

export default function MarketRankings({ sectors }) {
  const sectorList = sectors || [];
  const [sectorName, setSectorName] = useState('');

  useEffect(() => {
    if (!sectorName && sectorList.length) {
      setSectorName(sectorList[0].sector);
    }
  }, [sectorList, sectorName]);

  const activeSector = useMemo(
    () => sectorList.find((item) => item.sector === sectorName) || sectorList[0],
    [sectorList, sectorName],
  );

  const rankings = activeSector?.rankings;
  const entries = Object.entries(RANKING_LABELS);

  return (
    <div className="space-y-4">
      <section className="card">
        <h2 className="text-xl font-bold text-slate-900">Classements par secteur</h2>
        <p className="mt-2 text-sm text-slate-600">
          Chaque classement compare uniquement les sociétés cotées du secteur sélectionné.
        </p>
        <label className="mt-4 block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Secteur</span>
          <select
            value={activeSector?.sector || ''}
            onChange={(e) => setSectorName(e.target.value)}
            className="w-full max-w-md rounded-xl border border-slate-200 px-3 py-2 text-sm sm:w-auto"
          >
            {sectorList.map((sector) => (
              <option key={sector.sector} value={sector.sector}>
                {formatText(sector.sector)} ({sector.companies_count})
              </option>
            ))}
          </select>
        </label>
      </section>

      {activeSector ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {entries.map(([key, title]) => (
            <RankingList
              key={key}
              title={title}
              rows={rankings?.[key]}
              metricKey={METRIC_KEY_MAP[key]}
            />
          ))}
        </div>
      ) : (
        <p className="text-center text-sm text-slate-500">Aucun secteur disponible.</p>
      )}
    </div>
  );
}
