import { formatNumber, formatPercent, variationClass } from '../utils/format';

export default function MarketSummary({ summary }) {
  if (!summary) return null;

  const indices = (summary.indices || []).filter(
    (item, index, list) =>
      item?.name && list.findIndex((other) => other?.name === item.name) === index,
  );
  if (indices.length === 0) return null;

  return (
    <section className="card">
      <h2 className="mb-4 hidden text-lg font-bold text-slate-900 md:block">Marché global BRVM</h2>

      <div className="hidden grid-cols-2 gap-2 md:grid lg:grid-cols-4">
        {indices.map((index, indexPosition) => (
          <div
            key={`${index.name}-${index.last ?? indexPosition}`}
            className="rounded-lg border border-emerald-100 bg-emerald-50/60 px-3 py-2.5"
          >
            <div className="truncate text-[10px] font-semibold uppercase leading-tight tracking-wide text-emerald-800">
              {index.name}
            </div>
            <div className="mt-0.5 text-lg font-bold leading-tight text-slate-900">
              {formatNumber(index.last)}
            </div>
            <div className={`text-xs font-semibold ${variationClass(index.variation_pct)}`}>
              {formatPercent(index.variation_pct)}
            </div>
            <div className="mt-0.5 text-[10px] text-slate-500">
              Ouv. {formatNumber(index.opening)}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
