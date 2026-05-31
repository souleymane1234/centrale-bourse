export default function CompanyToolbar({
  sectors,
  sectorFilter,
  searchQuery,
  lastUpdate,
  onSectorChange,
  onSearchChange,
  onRefresh,
}) {
  const fieldClass =
    'h-10 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm';

  return (
    <section className="card flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-end">
      <label className="flex w-full flex-col gap-1 text-sm font-medium text-slate-700 sm:w-auto">
        Secteur
        <select
          value={sectorFilter}
          onChange={(event) => onSectorChange(event.target.value)}
          className={`${fieldClass} min-w-[180px]`}
        >
          <option value="">Tous les secteurs</option>
          {sectors.map((sector) => (
            <option key={sector} value={sector}>
              {sector}
            </option>
          ))}
        </select>
      </label>

      <label className="flex min-w-0 flex-1 flex-col gap-1 text-sm font-medium text-slate-700">
        Recherche
        <input
          type="search"
          value={searchQuery}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Société, ticker ou secteur"
          className={fieldClass}
        />
      </label>

      <div className="flex shrink-0 flex-col gap-1 sm:w-auto">
        <span className="hidden text-sm font-medium text-slate-700 sm:block sm:invisible" aria-hidden>
          Action
        </span>
        <button
          type="button"
          onClick={() => onRefresh?.()}
          className="h-10 w-full rounded-lg bg-brand-600 px-5 text-sm font-semibold text-white hover:bg-brand-700 sm:w-auto"
        >
          Actualiser
        </button>
      </div>

      {lastUpdate && (
        <span className="text-xs text-slate-500 lg:ml-auto">Dernière mise à jour: {lastUpdate}</span>
      )}
    </section>
  );
}
