import { useAuth } from '../../context/AuthContext';
import { formatDateTime } from '../../utils/format';

export default function SubscriptionSection() {
  const { user, paymentsEnabled } = useAuth();

  if (!paymentsEnabled) {
    return null;
  }

  const access = user?.access || {};
  const sub = user?.subscription || {};
  const plan = sub.plan;

  const statusLabel = () => {
    if (!access.has_access) return 'Expiré';
    if (access.is_trial) return 'Essai gratuit';
    if (access.is_paid) return 'Abonnement actif';
    return 'Actif';
  };

  const statusClass = access.has_access
    ? access.is_trial
      ? 'bg-amber-100 text-amber-900'
      : 'bg-emerald-100 text-emerald-800'
    : 'bg-rose-100 text-rose-800';

  return (
    <section className="card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Abonnement</h2>
          <p className="mt-1 text-sm text-slate-600">Informations sur votre accès à la plateforme.</p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClass}`}>
          {statusLabel()}
        </span>
      </div>

      <dl className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg bg-slate-50 px-4 py-3">
          <dt className="text-xs font-semibold uppercase text-slate-400">Plan</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-900">{plan?.name || '—'}</dd>
        </div>
        <div className="rounded-lg bg-slate-50 px-4 py-3">
          <dt className="text-xs font-semibold uppercase text-slate-400">Jours restants</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-900">
            {access.has_access ? `${sub.days_remaining ?? 0} jour(s)` : '0'}
          </dd>
        </div>
        <div className="rounded-lg bg-slate-50 px-4 py-3">
          <dt className="text-xs font-semibold uppercase text-slate-400">Début</dt>
          <dd className="mt-1 text-sm font-medium text-slate-800">
            {sub.started_at ? formatDateTime(sub.started_at) : '—'}
          </dd>
        </div>
        <div className="rounded-lg bg-slate-50 px-4 py-3">
          <dt className="text-xs font-semibold uppercase text-slate-400">Fin</dt>
          <dd className="mt-1 text-sm font-medium text-slate-800">
            {sub.expires_at ? formatDateTime(sub.expires_at) : '—'}
          </dd>
        </div>
      </dl>
    </section>
  );
}
