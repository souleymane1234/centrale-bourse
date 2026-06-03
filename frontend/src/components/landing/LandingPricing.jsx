import { useState } from 'react';
import { Check, CreditCard } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const MONTHLY_PRICE_FCFA = 2500;
const ANNUAL_DISCOUNT = 0.2;
const ANNUAL_MONTHLY_EQUIVALENT = Math.round(MONTHLY_PRICE_FCFA * (1 - ANNUAL_DISCOUNT));
const ANNUAL_TOTAL_FCFA = ANNUAL_MONTHLY_EQUIVALENT * 12;

const formatFcfa = (amount) => amount.toLocaleString('fr-FR');

const FEATURES = [
  'Toutes les sociétés cotées et cours du jour',
  'Analyses, graphiques et indicateurs techniques',
  'Comparaison par secteur et face-à-face',
  'Classements sectoriels et score investisseur',
  'Fil d’actualités boursières BRVM',
];

const MOBILE_MONEY = [
  { name: 'Wave', className: 'bg-[#1dc8ff] text-slate-900' },
  { name: 'Orange Money', className: 'bg-[#ff7900] text-white' },
  { name: 'MTN Money', className: 'bg-[#ffcc00] text-slate-900' },
  { name: 'Moov Money', className: 'bg-[#0066b3] text-white' },
];

export default function LandingPricing() {
  const { isAuthenticated, hasPlatformAccess } = useAuth();
  const [billing, setBilling] = useState('monthly');

  const isAnnual = billing === 'annual';
  const displayPrice = isAnnual ? ANNUAL_MONTHLY_EQUIVALENT : MONTHLY_PRICE_FCFA;

  const cta = (() => {
    if (!isAuthenticated) {
      return { to: '/profil', label: 'Démarrer l’essai gratuit' };
    }
    if (hasPlatformAccess) {
      return { to: '/', label: 'Accéder à la plateforme' };
    }
    return { to: '/profil', label: 'S’abonner maintenant' };
  })();

  return (
    <section id="tarifs" className="border-t border-slate-200/80 bg-white py-28 sm:py-32 lg:py-36">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Conçu pour chaque investisseur, débutant ou expérimenté
          </h2>
          <p className="mt-4 text-base text-slate-600 sm:text-lg">
            Essayez gratuitement pendant 5 jours, aucune carte de crédit requise.
          </p>

          <div
            className="mx-auto mt-8 inline-flex rounded-full border border-slate-200 bg-slate-100 p-1"
            role="group"
            aria-label="Type de facturation"
          >
            <button
              type="button"
              onClick={() => setBilling('annual')}
              className={`rounded-full px-5 py-2 text-sm font-semibold transition ${
                isAnnual ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Annuel
            </button>
            <button
              type="button"
              onClick={() => setBilling('monthly')}
              className={`rounded-full px-5 py-2 text-sm font-semibold transition ${
                !isAnnual ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Mensuel
            </button>
          </div>
        </div>

        <div className="mx-auto mt-14 max-w-lg">
          <article className="overflow-hidden rounded-2xl border-2 border-slate-900 bg-white shadow-[0_24px_60px_-24px_rgba(15,23,42,0.2)]">
            <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-5 sm:px-8">
              <div>
                <h3 className="text-xl font-bold text-slate-900">Abonnement Centrale Bourse</h3>
                <p className="mt-1 text-sm text-slate-600">
                  Accès complet à la plateforme d’analyse du marché régional.
                </p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1.5">
                <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-800">
                  5 jours offerts
                </span>
                {isAnnual ? (
                  <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                    −20 %
                  </span>
                ) : null}
              </div>
            </div>

            <div className="px-6 py-6 sm:px-8">
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-bold tracking-tight text-slate-900">
                  {formatFcfa(displayPrice)}
                </span>
                <span className="text-lg font-medium text-slate-600">FCFA / mois</span>
              </div>
              {isAnnual ? (
                <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-slate-500">
                  <span>
                    Facturé annuellement · {formatFcfa(ANNUAL_TOTAL_FCFA)} FCFA / an
                  </span>
                  <span className="rounded-md bg-emerald-100 px-2 py-0.5 text-xs font-bold uppercase tracking-wide text-emerald-800">
                    Économisez 20 %
                  </span>
                </div>
              ) : (
                <p className="mt-2 text-sm text-slate-500">Facturation mensuelle · renouvelable</p>
              )}
              {isAnnual ? (
                <p className="mt-1 text-xs text-slate-400 line-through">
                  {formatFcfa(MONTHLY_PRICE_FCFA)} FCFA / mois sans engagement annuel
                </p>
              ) : null}
            </div>

            <ul className="space-y-4 border-t border-slate-100 px-6 py-6 sm:px-8">
              {FEATURES.map((feature) => (
                <li key={feature} className="flex items-start gap-3 text-sm text-slate-700">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-sky-100 text-sky-700">
                    <Check className="h-3 w-3" strokeWidth={3} aria-hidden />
                  </span>
                  {feature}
                </li>
              ))}
            </ul>

            <div className="border-t border-slate-100 px-6 py-6 sm:px-8">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Moyens de paiement acceptés
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {MOBILE_MONEY.map((provider) => (
                  <span
                    key={provider.name}
                    className={`rounded-lg px-3 py-1.5 text-xs font-bold ${provider.className}`}
                  >
                    {provider.name}
                  </span>
                ))}
                <span className="inline-flex items-center gap-1.5 rounded-lg bg-[#1a1f71] px-3 py-1.5 text-xs font-bold text-white">
                  <CreditCard className="h-3.5 w-3.5" aria-hidden />
                  Visa
                </span>
              </div>
            </div>

            <div className="px-6 pb-8 sm:px-8">
              <Link
                to={cta.to}
                className="flex w-full items-center justify-center rounded-xl bg-slate-900 py-3.5 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                {cta.label}
              </Link>
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}
