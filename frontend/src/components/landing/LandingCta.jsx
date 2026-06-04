import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function LandingCta() {
  const { isAuthenticated } = useAuth();

  const primary = (() => {
    if (!isAuthenticated) {
      return { to: '/profil', label: 'Essayer gratuitement' };
    }
    return { to: '/', label: 'Accéder à la plateforme' };
  })();

  return (
    <section className="bg-slate-950 py-24 sm:py-28 lg:py-32">
      <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
        <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl lg:text-[2.5rem] lg:leading-tight">
          Commencez à investir avec clarté dès aujourd&apos;hui
        </h2>
        <p className="mx-auto mt-5 max-w-2xl text-base text-slate-300 sm:text-lg">
          Créez un compte gratuit et explorez les cours, analyses et actualités de la BRVM.
        </p>

        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row sm:gap-6">
          <Link
            to={primary.to}
            className="inline-flex min-w-[200px] items-center justify-center rounded-full bg-slate-200 px-8 py-3.5 text-sm font-semibold text-slate-900 transition hover:bg-white"
          >
            {primary.label}
          </Link>
          <a
            href="#fonctionnalites"
            className="text-sm font-medium text-slate-300 underline-offset-4 transition hover:text-white hover:underline"
          >
            Voir les fonctionnalités
          </a>
        </div>
      </div>
    </section>
  );
}
