import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  deleteAlert,
  fetchAlerts,
  fetchWatchlist,
  removeWatchlistItem,
  updateAlert,
} from '../api/userFeatures';
import CompanyLogo from '../components/CompanyLogo';
import Spinner from '../components/Spinner';
import { useAuth } from '../context/AuthContext';
import { companyPath } from '../utils/routing';
import { formatCurrency, formatPercent, formatText, variationBadgeClass } from '../utils/format';

export default function FollowPage() {
  const { isAuthenticated, hasPlatformAccess } = useAuth();
  const [tab, setTab] = useState('watchlist');
  const [watchlist, setWatchlist] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [notificationsNote, setNotificationsNote] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    if (!isAuthenticated || !hasPlatformAccess) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [watchData, alertData] = await Promise.all([fetchWatchlist(), fetchAlerts()]);
      setWatchlist(watchData.items || []);
      setAlerts(alertData.alerts || []);
      setNotificationsNote(alertData.notifications_note || '');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, hasPlatformAccess]);

  useEffect(() => {
    load();
  }, [load]);

  const handleRemoveWatch = async (ticker) => {
    await removeWatchlistItem(ticker);
    setWatchlist((items) => items.filter((item) => item.ticker !== ticker));
  };

  const handleToggleAlert = async (alert) => {
    const data = await updateAlert(alert.id, { is_active: !alert.is_active });
    setAlerts((rows) => rows.map((row) => (row.id === alert.id ? data.alert : row)));
  };

  const handleDeleteAlert = async (alertId) => {
    await deleteAlert(alertId);
    setAlerts((rows) => rows.filter((row) => row.id !== alertId));
  };

  if (!isAuthenticated) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10 text-center">
        <p className="text-slate-600">Connectez-vous pour gérer votre liste de suivi et vos alertes.</p>
        <Link to="/profil" className="mt-4 inline-block text-sm font-semibold text-brand-700">
          Se connecter →
        </Link>
      </div>
    );
  }

  if (!hasPlatformAccess) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10 text-center">
        <p className="text-slate-600">Un abonnement actif est requis pour utiliser le suivi et les alertes.</p>
        <Link to="/profil" className="mt-4 inline-block text-sm font-semibold text-brand-700">
          Mon abonnement →
        </Link>
      </div>
    );
  }

  if (loading) {
    return <Spinner label="Chargement de votre suivi..." />;
  }

  return (
    <div className="mx-auto max-w-7xl space-y-5 px-4 py-6 sm:px-6">
      <header>
        <h1 className="text-2xl font-bold text-slate-900">Suivi & alertes</h1>
        <p className="mt-1 text-sm text-slate-600">
          Liste de suivi (jusqu&apos;à 50 sociétés) et alertes de cours (jusqu&apos;à 20 actives).
        </p>
      </header>

      {error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {error}
        </div>
      ) : null}

      <div className="inline-flex rounded-full border border-slate-200 bg-slate-100 p-1">
        <button
          type="button"
          onClick={() => setTab('watchlist')}
          className={`rounded-full px-4 py-2 text-sm font-semibold ${
            tab === 'watchlist' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'
          }`}
        >
          Liste de suivi ({watchlist.length})
        </button>
        <button
          type="button"
          onClick={() => setTab('alerts')}
          className={`rounded-full px-4 py-2 text-sm font-semibold ${
            tab === 'alerts' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'
          }`}
        >
          Alertes ({alerts.filter((a) => a.is_active).length})
        </button>
      </div>

      {tab === 'watchlist' ? (
        <section className="card">
          {watchlist.length === 0 ? (
            <p className="text-sm text-slate-600">
              Aucune société suivie. Ajoutez-en depuis une fiche société (étoile en haut à droite).
            </p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {watchlist.map((item) => {
                const company = item.company || {};
                return (
                  <li key={item.id} className="flex flex-wrap items-center gap-4 py-4">
                    <CompanyLogo
                      name={company.name}
                      symbol={company.symbol}
                      ticker={item.ticker}
                      code={company.code}
                    />
                    <div className="min-w-0 flex-1">
                      <Link
                        to={companyPath(item.ticker)}
                        className="font-semibold text-slate-900 hover:text-brand-700"
                      >
                        {formatText(company.name || item.ticker)}
                      </Link>
                      <p className="text-xs text-slate-500">
                        {formatText(company.symbol || item.ticker)}
                        {company.sector ? ` · ${company.sector}` : ''}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-slate-900">{formatCurrency(company.price)}</p>
                      {company.variation != null ? (
                        <span
                          className={`text-xs font-semibold ${variationBadgeClass(company.variation)}`}
                        >
                          {company.variation > 0 ? '+' : ''}
                          {formatPercent(company.variation)}
                        </span>
                      ) : null}
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveWatch(item.ticker)}
                      className="text-xs font-semibold text-rose-700 hover:text-rose-800"
                    >
                      Retirer
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      ) : (
        <section className="space-y-3">
          {notificationsNote ? (
            <p className="rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900">
              {notificationsNote}
            </p>
          ) : null}
          <div className="card">
            {alerts.length === 0 ? (
              <p className="text-sm text-slate-600">
                Aucune alerte. Créez-en depuis une fiche société (cloche en haut à droite).
              </p>
            ) : (
              <ul className="divide-y divide-slate-100">
                {alerts.map((alert) => {
                  const company = alert.company || {};
                  const label =
                    alert.direction === 'above'
                      ? `≥ ${formatCurrency(alert.target_price)}`
                      : `≤ ${formatCurrency(alert.target_price)}`;
                  return (
                    <li key={alert.id} className="py-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <Link
                            to={companyPath(alert.ticker)}
                            className="font-semibold text-slate-900 hover:text-brand-700"
                          >
                            {formatText(company.name || alert.ticker)}
                          </Link>
                          <p className="mt-1 text-sm text-slate-600">
                            Alerte {label} · cours actuel{' '}
                            {formatCurrency(alert.current_price)}
                          </p>
                          {alert.is_triggered ? (
                            <span className="mt-2 inline-block rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">
                              Seuil atteint
                            </span>
                          ) : null}
                          {!alert.is_active ? (
                            <span className="mt-2 ml-2 inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600">
                              Pause
                            </span>
                          ) : null}
                        </div>
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => handleToggleAlert(alert)}
                            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700"
                          >
                            {alert.is_active ? 'Pause' : 'Activer'}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteAlert(alert.id)}
                            className="rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-700"
                          >
                            Supprimer
                          </button>
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
