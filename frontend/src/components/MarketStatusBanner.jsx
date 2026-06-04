import { Clock3 } from 'lucide-react';
import { getBrvmMarketStatusFallback } from '../utils/brvmMarketStatus';

function StatusDot({ open }) {
  if (open) {
    return (
      <span className="relative flex h-2.5 w-2.5 shrink-0" aria-hidden>
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
        <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
      </span>
    );
  }

  return <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-slate-400" aria-hidden />;
}

export default function MarketStatusBanner({ status }) {
  const resolved = status || getBrvmMarketStatusFallback();
  if (!resolved) return null;

  const isOpen = Boolean(resolved.is_open);
  const openLabel = resolved.session_open || '9h30';
  const closeLabel = resolved.session_close || '15h30';

  return (
    <section
      className={`flex flex-col gap-3 rounded-xl border px-4 py-3 sm:flex-row sm:items-center sm:justify-between ${
        isOpen
          ? 'border-emerald-200 bg-emerald-50/80'
          : 'border-slate-200 bg-slate-50'
      }`}
      aria-live="polite"
    >
      <div className="flex items-start gap-3">
        <StatusDot open={isOpen} />
        <div>
          <p
            className={`text-sm font-bold ${
              isOpen ? 'text-emerald-900' : 'text-slate-800'
            }`}
          >
            {resolved.label || (isOpen ? 'Marché ouvert' : 'Marché fermé')}
          </p>
          {resolved.detail ? (
            <p className="mt-0.5 text-sm text-slate-600">{resolved.detail}</p>
          ) : null}
        </div>
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-500 sm:text-right">
        <Clock3 className="h-3.5 w-3.5 shrink-0" aria-hidden />
        <span>
          Séance lun–ven · {openLabel} – {closeLabel} · Abidjan
        </span>
      </div>
    </section>
  );
}
