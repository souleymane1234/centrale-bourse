import { formatGrowthPercent, formatNumber, formatText } from '../utils/format';

function FinancialTable({ headers, rows }) {
  return (
    <div className="max-w-full overflow-x-auto overscroll-x-contain">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-slate-500">
            {headers.map((header) => (
              <th key={header} className="whitespace-nowrap px-2 py-2 font-semibold">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-b border-slate-100">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="whitespace-nowrap px-2 py-2 text-slate-800">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MetricLine({ label, value }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-slate-100 py-2 last:border-0">
      <span className="shrink-0 text-xs text-slate-500">{label}</span>
      <span className="text-right text-xs font-semibold text-slate-800">{value}</span>
    </div>
  );
}

function YearCard({ entry }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-slate-50/70 p-3">
      <h4 className="mb-2 text-sm font-bold text-slate-900">{formatText(entry.year)}</h4>
      <MetricLine label="Chiffre d'affaires" value={formatNumber(entry.revenue_mfcfa)} />
      <MetricLine label="Croissance CA" value={formatGrowthPercent(entry.revenue_growth_pct)} />
      <MetricLine label="Rés. net" value={formatNumber(entry.net_income_mfcfa)} />
      <MetricLine label="Croissance RN" value={formatGrowthPercent(entry.net_income_growth_pct)} />
      <MetricLine label="BNPA" value={formatNumber(entry.eps_fcfa)} />
      <MetricLine label="PER" value={formatNumber(entry.pe_ratio)} />
      <MetricLine label="Dividende" value={formatNumber(entry.dividend_per_share_fcfa)} />
    </article>
  );
}

const TABLE_HEADERS = [
  'Année',
  'CA',
  'Croiss. CA',
  'Rés. net',
  'Croiss. RN',
  'BNPA',
  'PER',
  'Dividende',
];

export default function FinancialStatementsSection({ statements = [] }) {
  if (!statements.length) return null;

  const sorted = [...statements].sort((a, b) => (b.year || 0) - (a.year || 0));
  const rows = sorted.map((entry) => [
    formatText(entry.year),
    formatNumber(entry.revenue_mfcfa),
    formatGrowthPercent(entry.revenue_growth_pct),
    formatNumber(entry.net_income_mfcfa),
    formatGrowthPercent(entry.net_income_growth_pct),
    formatNumber(entry.eps_fcfa),
    formatNumber(entry.pe_ratio),
    formatNumber(entry.dividend_per_share_fcfa),
  ]);

  return (
    <>
      <div className="space-y-3 md:hidden">
        {sorted.map((entry) => (
          <YearCard key={entry.year} entry={entry} />
        ))}
      </div>
      <div className="hidden md:block">
        <FinancialTable headers={TABLE_HEADERS} rows={rows} />
      </div>
    </>
  );
}
