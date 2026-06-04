import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { formatDateTime } from '../../utils/format';

export default function ReferralSection() {
  const { user, paymentsEnabled } = useAuth();

  if (!paymentsEnabled) {
    return null;
  }

  const referral = user?.referral || {};
  const [copied, setCopied] = useState(false);

  const copyCode = async () => {
    if (!referral.referral_code) return;
    try {
      await navigator.clipboard.writeText(referral.referral_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  return (
    <section className="card">
      <h2 className="text-lg font-bold text-slate-900">Parrainage</h2>
      <p className="mt-1 text-sm text-slate-600">
        Gagnez {referral.commission_rate_percent || 20}% sur chaque abonnement et renouvellement de vos filleuls.
      </p>

      <div className="mt-4 flex flex-wrap items-center gap-3 rounded-xl border border-dashed border-brand-300 bg-brand-50/50 px-4 py-4">
        <div>
          <p className="text-xs font-semibold uppercase text-slate-500">Votre code</p>
          <p className="font-mono text-2xl font-bold tracking-wider text-brand-800">
            {referral.referral_code || '—'}
          </p>
        </div>
        <button
          type="button"
          onClick={copyCode}
          className="rounded-lg bg-white px-4 py-2 text-sm font-semibold text-brand-700 shadow-sm ring-1 ring-brand-200 hover:bg-brand-50"
        >
          {copied ? 'Copié !' : 'Copier'}
        </button>
      </div>

      <p className="mt-3 text-xs text-slate-500">
        Partagez ce code à l&apos;inscription. Commission créditée sur votre solde à chaque paiement.
      </p>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg bg-slate-50 px-4 py-3">
          <p className="text-xs font-semibold uppercase text-slate-400">Solde</p>
          <p className="mt-1 text-lg font-bold text-slate-900">
            {(referral.balance_fcfa ?? 0).toLocaleString('fr-FR')} FCFA
          </p>
        </div>
        <div className="rounded-lg bg-slate-50 px-4 py-3">
          <p className="text-xs font-semibold uppercase text-slate-400">Filleuls</p>
          <p className="mt-1 text-lg font-bold text-slate-900">{referral.referred_users_count ?? 0}</p>
        </div>
        <div className="rounded-lg bg-slate-50 px-4 py-3">
          <p className="text-xs font-semibold uppercase text-slate-400">Commissions totales</p>
          <p className="mt-1 text-lg font-bold text-slate-900">
            {(referral.total_commission_fcfa ?? 0).toLocaleString('fr-FR')} FCFA
          </p>
        </div>
      </div>

      {(referral.recent_earnings || []).length > 0 ? (
        <div className="mt-5">
          <h3 className="text-sm font-semibold text-slate-800">Dernières commissions</h3>
          <ul className="mt-2 divide-y divide-slate-100 rounded-xl border border-slate-200">
            {referral.recent_earnings.map((row) => (
              <li key={row.id} className="flex items-center justify-between px-4 py-3 text-sm">
                <span className="text-slate-600">
                  {row.kind === 'renewal' ? 'Renouvellement' : 'Abonnement'} ·{' '}
                  {row.created_at ? formatDateTime(row.created_at) : ''}
                </span>
                <span className="font-semibold text-emerald-700">
                  +{row.commission_fcfa?.toLocaleString('fr-FR')} FCFA
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-500">Aucune commission pour le moment.</p>
      )}
    </section>
  );
}
