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

  return (
    <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:py-6">
      <header className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Mon profil</h1>
          <p className="mt-0.5 text-sm text-slate-600">
            Compte, abonnement mensuel, parrainage et solde.
          </p>
        </div>
        {isAuthenticated ? (
          <button
            type="button"
            onClick={() => logout()}
            className="self-start rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            Déconnexion
          </button>
        ) : null}
      </header>

      {!isAuthenticated ? (
        <AuthForms />
      ) : (
        <div className="grid gap-5 lg:grid-cols-2">
          <div className="space-y-5">
            <ProfileInfoSection key={user?.email} />
            <SubscriptionSection />
          </div>
          <ReferralSection />
        </div>
      )}
    </div>
  );
}
