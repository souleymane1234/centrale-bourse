import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { formatDateTime } from '../../utils/format';

export default function SubscriptionSection() {
  const { user, subscribe } = useAuth();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const access = user?.access || {};
  const sub = user?.subscription || {};
  const plan = sub.plan;
  const priceLabel = plan?.price_fcfa
    ? `${plan.price_fcfa.toLocaleString('fr-FR')} FCFA`
    : '2 500 FCFA';

  const onSubscribe = async () => {
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      await subscribe();
      setMessage('Abonnement mensuel activé pour 30 jours.');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

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
          <p className="mt-1 text-sm text-slate-600">Durée : 1 mois (30 jours) — renouvelable.</p>
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

      {access.is_trial && access.has_access ? (
        <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Cadeau : {sub.days_remaining} jour(s) d&apos;essai gratuit avant de souscrire l&apos;abonnement
          mensuel ({priceLabel}/mois).
        </p>
      ) : null}

      {!access.has_access ? (
        <p className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          Votre accès a expiré. Souscrivez l&apos;abonnement pour retrouver la plateforme.
        </p>
      ) : null}

      <div className="mt-5 flex flex-wrap gap-3">
        {(access.can_subscribe || !access.has_access) && !access.is_paid ? (
          <button
            type="button"
            onClick={onSubscribe}
            disabled={busy}
            className="rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {busy ? 'Paiement...' : `S'abonner — ${priceLabel} / mois`}
          </button>
        ) : null}
        {access.is_paid && access.has_access ? (
          <button
            type="button"
            onClick={onSubscribe}
            disabled={busy}
            className="rounded-xl border border-brand-200 bg-brand-50 px-5 py-2.5 text-sm font-semibold text-brand-800 hover:bg-brand-100 disabled:opacity-60"
          >
            {busy ? 'Traitement...' : 'Renouveler (1 mois)'}
          </button>
        ) : null}
        {!access.has_access ? (
          <Link
            to="/bienvenue"
            className="rounded-xl border border-slate-200 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            Voir la page d&apos;accueil
          </Link>
        ) : null}
      </div>

      {message ? <p className="mt-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="mt-3 text-sm text-rose-700">{error}</p> : null}
      <p className="mt-3 text-xs text-slate-500">
        Paiement simulé en développement (Mobile Money / carte à brancher en production).
      </p>
    </section>
  );
}
