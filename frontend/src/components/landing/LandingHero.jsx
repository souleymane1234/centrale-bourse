import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import dashboardPreview from '../../assets/landing-dashboard.png';

function ChartDecoration() {
  return (
    <svg
      className="pointer-events-none absolute -bottom-8 -right-4 h-64 w-80 opacity-[0.12] sm:h-80 sm:w-96"
      viewBox="0 0 200 120"
      fill="none"
      aria-hidden
    >
      <rect x="12" y="50" width="14" height="40" fill="#10b981" rx="2" />
      <rect x="32" y="35" width="14" height="55" fill="#ef4444" rx="2" />
      <rect x="52" y="45" width="14" height="45" fill="#10b981" rx="2" />
      <rect x="72" y="25" width="14" height="65" fill="#10b981" rx="2" />
      <rect x="92" y="40" width="14" height="50" fill="#ef4444" rx="2" />
      <rect x="112" y="30" width="14" height="60" fill="#10b981" rx="2" />
      <rect x="132" y="55" width="14" height="35" fill="#ef4444" rx="2" />
      <rect x="152" y="20" width="14" height="70" fill="#10b981" rx="2" />
      <rect x="172" y="38" width="14" height="52" fill="#10b981" rx="2" />
    </svg>
  );
}

export default function LandingHero() {
  const { isAuthenticated, hasPlatformAccess } = useAuth();

  const primaryCta = (() => {
    if (!isAuthenticated) {
      return { to: '/profil', label: 'Commencer gratuitement' };
    }
    if (hasPlatformAccess) {
      return { to: '/', label: 'Accéder à la plateforme' };
    }
    return { to: '/profil', label: "S'abonner" };
  })();

  return (
    <section className="relative overflow-hidden">
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_30%_20%,rgba(16,185,129,0.08),transparent_55%),radial-gradient(ellipse_at_80%_60%,rgba(30,58,110,0.06),transparent_50%)]"
        aria-hidden
      />

      <div className="relative mx-auto grid max-w-7xl items-center gap-14 px-4 py-24 sm:px-6 sm:py-28 lg:grid-cols-2 lg:gap-16 lg:py-36 lg:px-8">
        <div className="max-w-xl">
          <p className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm">
            <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden />
            Nouveau : palmarès et cotations BRVM actualisés
          </p>

          <h1 className="mt-6 text-3xl font-bold leading-[1.15] tracking-tight text-slate-900 sm:text-4xl lg:text-[2.65rem]">
            Investissez à la BRVM en toute confiance et non au hasard.
          </h1>

          <p className="mt-5 text-base leading-relaxed text-slate-600 sm:text-lg">
            Fini les PDF épars et les tableurs artisanaux. BRVM Agent centralise les cours,
            les analyses sectorielles, les comparatifs et l&apos;actualité du marché régional
            pour décider avec des données claires.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link
              to={primaryCta.to}
              className="inline-flex items-center justify-center rounded-xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white shadow-md transition hover:bg-slate-800"
            >
              {primaryCta.label}
            </Link>
            <a
              href="#fonctionnalites"
              className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-800 shadow-sm transition hover:bg-slate-50"
            >
              Voir comment ça marche
            </a>
          </div>

          <p className="mt-4 text-xs text-slate-500">5 jours d&apos;essai offerts · sans carte bancaire</p>
        </div>

        <div className="relative lg:pl-4">
          <ChartDecoration />
          <div className="relative">
            <img
              src={dashboardPreview}
              alt="Aperçu du tableau de bord BRVM Agent : palmarès, indices et sociétés cotées"
              className="block h-auto w-full max-w-full drop-shadow-[0_20px_50px_rgba(15,23,42,0.35)]"
              loading="eager"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
