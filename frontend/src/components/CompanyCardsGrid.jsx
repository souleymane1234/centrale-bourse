import { formatCurrency, formatPercent, formatText, variationClass } from '../utils/format';
import CompanyLogo from './CompanyLogo';

export default function CompanyCardsGrid({ companies, onSelect }) {
  if (!companies.length) {
    return (
      <div className="card text-sm text-slate-600">
        Aucune société ne correspond à votre recherche.
      </div>
    );
  }

  return (
    <section>
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-base font-bold text-slate-900">
          Sociétés cotées
          <span className="ml-2 text-sm font-normal text-slate-500">
            ({companies.length})
          </span>
        </h2>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {companies.map((company) => {
          const variation = company.variation;

          return (
            <button
              key={company.ticker}
              type="button"
              onClick={() => onSelect(company.ticker)}
              className="group rounded-xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:border-brand-500 hover:shadow-md"
            >
              <div className="flex items-start gap-3">
                <CompanyLogo
                  name={company.name}
                  symbol={company.symbol}
                  ticker={company.ticker}
                  code={company.code}
                />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-bold text-slate-900 group-hover:text-brand-700">
                    {formatText(company.name)}
                  </p>
                  <p className="mt-0.5 text-xs font-semibold text-slate-500">
                    {formatText(company.symbol || company.ticker)}
                  </p>
                  <p className="mt-1.5 line-clamp-2 text-xs leading-snug text-slate-600">
                    <span className="font-medium text-slate-400">Secteur · </span>
                    {formatText(company.sector)}
                  </p>
                </div>
              </div>

              <div className="mt-3 flex items-end justify-between gap-2 border-t border-slate-100 pt-3">
                <div>
                  <p className="text-[10px] uppercase tracking-wide text-slate-400">Cours</p>
                  <p className="text-lg font-bold text-slate-900">
                    {formatCurrency(company.price)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-[10px] uppercase tracking-wide text-slate-400">Variation</p>
                  <p className={`text-sm font-bold ${variationClass(variation)}`}>
                    {formatPercent(variation)}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
