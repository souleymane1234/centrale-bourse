import { Check } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const FEATURES = [
  'Toutes les sociétés cotées et cours du jour',
  'Analyses, graphiques et indicateurs techniques',
  'Comparaison par secteur et face-à-face',
  'Classements sectoriels et score investisseur',
  'Fil d’actualités boursières BRVM',
];

export default function LandingPricing() {
  const { isAuthenticated, hasPlatformAccess } = useAuth();

  const cta = (() => {
    if (!isAuthenticated) {
      return { to: '/profil', label: 'Créer un compte gratuit' };
    }
    if (hasPlatformAccess) {
      return { to: '/', label: 'Accéder à la plateforme' };
    }
    return { to: '/profil', label: 'Se connecter' };
  })();

  return (
    <section id="tarifs" className="border-t border-slate-200/80 bg-white py-28 sm:py-32 lg:py-36">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Conçu pour chaque investisseur, débutant ou expérimenté
          </h2>
          <p className="mt-4 text-base text-slate-600 sm:text-lg">
            Accès complet à la plateforme après création de compte. La facturation sera proposée
            ultérieurement.
          </p>
        </div>

        <div className="mx-auto mt-14 max-w-lg">
          <article className="overflow-hidden rounded-2xl border-2 border-slate-900 bg-white shadow-[0_24px_60px_-24px_rgba(15,23,42,0.2)]">
            <div className="border-b border-slate-100 px-6 py-5 sm:px-8">
              <h3 className="text-xl font-bold text-slate-900">Centrale Bourse</h3>
              <p className="mt-1 text-sm text-slate-600">
                Accès complet à la plateforme d’analyse du marché régional.
              </p>
            </div>

            <ul className="space-y-4 px-6 py-6 sm:px-8">
              {FEATURES.map((feature) => (
                <li key={feature} className="flex items-start gap-3 text-sm text-slate-700">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-sky-100 text-sky-700">
                    <Check className="h-3 w-3" strokeWidth={3} aria-hidden />
                  </span>
                  {feature}
                </li>
              ))}
            </ul>

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
