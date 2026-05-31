import { useMemo, useState } from 'react';
import { formatDateTime, formatPercent, formatText, variationClass } from '../utils/format';
import SectorComparisonMatrix from './compare/SectorComparisonMatrix';
import SectorRankingsPanel from './compare/SectorRankingsPanel';

function SectorBlock({ sector, defaultOpen }) {
  const [open, setOpen] = useState(defaultOpen);
  const [view, setView] = useState('matrix');

  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-card">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between gap-3 border-b border-slate-100 px-4 py-3 text-left hover:bg-slate-50/80"
      >
        <div className="min-w-0">
          <h3 className="text-base font-bold text-slate-900 md:text-lg">{formatText(sector.sector)}</h3>
          <p className="mt-0.5 text-xs text-slate-500">
            {sector.companies_count} sociétés · variation moy.{' '}
            <span className={variationClass(sector.avg_variation_pct)}>
              {formatPercent(sector.avg_variation_pct)}
            </span>
          </p>
        </div>
        <span className="shrink-0 text-slate-400" aria-hidden>
          {open ? '▾' : '▸'}
        </span>
      </button>

      {open && (
        <div className="space-y-4 p-4">
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setView('matrix')}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${
                view === 'matrix' ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-700'
              }`}
            >
              Tableau KPI
            </button>
            <button
              type="button"
              onClick={() => setView('rankings')}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${
                view === 'rankings' ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-700'
              }`}
            >
              Classements
            </button>
          </div>

          {view === 'matrix' ? (
            <SectorComparisonMatrix companies={sector.companies} />
          ) : (
            <SectorRankingsPanel rankings={sector.rankings} />
          )}
        </div>
      )}
    </section>
  );
}

export default function SectorComparisonView({ data }) {
  const sectors = data?.sectors || [];
  const [filter, setFilter] = useState('');

  const filteredSectors = useMemo(() => {
    const query = filter.trim().toLowerCase();
    if (!query) return sectors;
    return sectors
      .map((sector) => {
        const sectorMatch = sector.sector?.toLowerCase().includes(query);
        const companies = sector.companies.filter(
          (company) =>
            sectorMatch ||
            company.name?.toLowerCase().includes(query) ||
            company.symbol?.toLowerCase().includes(query) ||
            company.ticker?.toLowerCase().includes(query),
        );
        if (!companies.length) return null;
        return { ...sector, companies, companies_count: companies.length };
      })
      .filter(Boolean);
  }, [filter, sectors]);

  return (
    <div className="space-y-6">
      <section className="card">
        <h2 className="text-xl font-bold text-slate-900">Comparaison par secteur</h2>
        <p className="mt-2 text-sm text-slate-600">
          Même disposition que les plateformes pro : KPI en lignes, sociétés en colonnes, regroupés par
          thème.
        </p>
        <dl className="mt-4 grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl bg-slate-50 px-4 py-3">
            <dt className="text-xs text-slate-500">Secteurs</dt>
            <dd className="text-lg font-bold text-slate-900">{data?.sectors_count ?? 0}</dd>
          </div>
          <div className="rounded-xl bg-slate-50 px-4 py-3">
            <dt className="text-xs text-slate-500">Sociétés cotées</dt>
            <dd className="text-lg font-bold text-slate-900">{data?.quoted_companies_count ?? 0}</dd>
          </div>
          <div className="rounded-xl bg-slate-50 px-4 py-3">
            <dt className="text-xs text-slate-500">Mise à jour</dt>
            <dd className="text-sm font-semibold text-slate-900">{formatDateTime(data?.generated_at)}</dd>
          </div>
        </dl>
        <input
          type="search"
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
          placeholder="Filtrer par secteur ou société…"
          className="mt-4 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
        />
      </section>

      {filteredSectors.length === 0 ? (
        <p className="text-center text-sm text-slate-500">Aucun résultat pour ce filtre.</p>
      ) : (
        filteredSectors.map((sector, index) => (
          <SectorBlock key={sector.sector} sector={sector} defaultOpen={index < 2} />
        ))
      )}
    </div>
  );
}
