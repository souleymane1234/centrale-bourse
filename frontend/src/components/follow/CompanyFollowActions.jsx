import { useCallback, useEffect, useState } from 'react';
import { Bell, Star } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  addWatchlistItem,
  createAlert,
  fetchWatchlistStatus,
  removeWatchlistItem,
} from '../../api/userFeatures';
import AlertFormModal from './AlertFormModal';

export default function CompanyFollowActions({ ticker, companyName, currentPrice }) {
  const { isAuthenticated, hasPlatformAccess } = useAuth();
  const [inWatchlist, setInWatchlist] = useState(false);
  const [watchBusy, setWatchBusy] = useState(false);
  const [alertOpen, setAlertOpen] = useState(false);

  const loadStatus = useCallback(async () => {
    if (!isAuthenticated || !ticker) return;
    try {
      const data = await fetchWatchlistStatus(ticker);
      setInWatchlist(Boolean(data.in_watchlist));
    } catch {
      setInWatchlist(false);
    }
  }, [isAuthenticated, ticker]);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const toggleWatchlist = async () => {
    if (!isAuthenticated) return;
    setWatchBusy(true);
    try {
      if (inWatchlist) {
        await removeWatchlistItem(ticker);
        setInWatchlist(false);
      } else {
        await addWatchlistItem(ticker);
        setInWatchlist(true);
      }
    } catch {
      /* erreur affichée via profil si besoin */
    } finally {
      setWatchBusy(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <Link
        to="/profil"
        className="text-xs font-medium text-brand-700 hover:text-brand-800"
        title="Connectez-vous pour suivre cette société"
      >
        Suivre
      </Link>
    );
  }

  if (!hasPlatformAccess) {
    return (
      <Link
        to="/profil"
        className="text-xs font-medium text-amber-800 hover:text-amber-900"
        title="Abonnement requis"
      >
        Activer l&apos;accès
      </Link>
    );
  }

  return (
    <>
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={toggleWatchlist}
          disabled={watchBusy}
          className={`rounded-lg p-2 transition ${
            inWatchlist
              ? 'text-amber-500 hover:bg-amber-50'
              : 'text-slate-400 hover:bg-white/60 hover:text-slate-600'
          }`}
          aria-label={inWatchlist ? 'Retirer de la liste de suivi' : 'Ajouter à la liste de suivi'}
          title={inWatchlist ? 'Dans votre liste de suivi' : 'Ajouter à la liste de suivi'}
        >
          <Star className={`h-5 w-5 ${inWatchlist ? 'fill-current' : ''}`} strokeWidth={1.75} />
        </button>
        <button
          type="button"
          onClick={() => setAlertOpen(true)}
          className="rounded-lg p-2 text-slate-400 transition hover:bg-white/60 hover:text-slate-600"
          aria-label="Créer une alerte de cours"
          title="Alerte de cours"
        >
          <Bell className="h-5 w-5" strokeWidth={1.75} />
        </button>
      </div>

      <AlertFormModal
        open={alertOpen}
        onClose={() => setAlertOpen(false)}
        ticker={ticker}
        companyName={companyName}
        currentPrice={currentPrice}
        onSubmit={createAlert}
      />
    </>
  );
}
