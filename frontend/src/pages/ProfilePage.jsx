import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AuthForms from '../components/profile/AuthForms';
import ProfileInfoSection from '../components/profile/ProfileInfoSection';
import ReferralSection from '../components/profile/ReferralSection';
import SubscriptionSection from '../components/profile/SubscriptionSection';
import Spinner from '../components/Spinner';

export default function ProfilePage() {
  const { user, loading, logout, isAuthenticated } = useAuth();

  if (loading) {
    return <Spinner label="Chargement du profil..." />;
  }

  if (!isAuthenticated) {
    return (
      <div className="mx-auto flex min-h-[calc(100dvh-9rem)] w-full max-w-7xl flex-col items-center justify-center px-4 py-8 text-center sm:px-6 md:min-h-[calc(100dvh-7rem)]">
        <header className="mb-6 w-full max-w-lg">
          <h1 className="text-2xl font-bold text-slate-900">Mon profil</h1>
          <p className="mt-2 text-sm text-slate-600">
            Connectez-vous ou créez un compte pour accéder à la plateforme et gérer votre suivi.
          </p>
        </header>

        <AuthForms />

        <footer className="mt-8 flex flex-wrap items-center justify-center gap-4 text-xs text-slate-500">
          <Link to="/cgu" className="hover:text-slate-800">
            Conditions générales
          </Link>
          <Link to="/confidentialite" className="hover:text-slate-800">
            Politique de confidentialité
          </Link>
        </footer>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:py-6">
      <header className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Mon profil</h1>
          <p className="mt-0.5 text-sm text-slate-600">Compte, suivi et alertes.</p>
        </div>
        <button
          type="button"
          onClick={() => logout()}
          className="self-start rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          Déconnexion
        </button>
      </header>

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="space-y-5">
          <ProfileInfoSection key={user?.email} />
          <SubscriptionSection />
          <section className="card">
            <h2 className="text-lg font-bold text-slate-900">Suivi & alertes</h2>
            <p className="mt-1 text-sm text-slate-600">
              Gérez votre liste de suivi et vos alertes de cours.
            </p>
            <Link
              to="/suivi"
              className="mt-4 inline-flex rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-slate-800"
            >
              Ouvrir mon suivi
            </Link>
          </section>
        </div>
        <ReferralSection />
      </div>

      <footer className="mt-8 flex flex-wrap gap-4 text-xs text-slate-500">
        <Link to="/cgu" className="hover:text-slate-800">
          Conditions générales
        </Link>
        <Link to="/confidentialite" className="hover:text-slate-800">
          Politique de confidentialité
        </Link>
      </footer>
    </div>
  );
}
