import { useEffect, useState } from 'react';
import { fetchCompareBySector } from '../api/client';
import HeadToHeadCompare from '../components/compare/HeadToHeadCompare';
import InvestorScoreTable from '../components/compare/InvestorScoreTable';
import MarketRankings from '../components/compare/MarketRankings';
import SectorComparisonView from '../components/SectorComparisonView';
import Spinner from '../components/Spinner';

const TABS = [
  { id: 'sector', label: 'Par secteur' },
  { id: 'head', label: '2 entreprises' },
  { id: 'rankings', label: 'Classements' },
  { id: 'score', label: 'Score investisseur' },
];

export default function ComparePage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState('sector');

  useEffect(() => {
    fetchCompareBySector()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Spinner label="Chargement de la comparaison..." />;
  }

  if (error && !data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12">
        <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {error}
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold text-slate-900">Comparer les actions</h1>
        <p className="text-sm text-slate-600">
          Comparez les sociétés au sein de leur secteur : rentabilité, croissance, dividendes,
          valorisation et performance boursière.
        </p>
      </header>

      <nav className="flex flex-wrap gap-2 border-b border-slate-200 pb-1">
        {TABS.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setTab(item.id)}
            className={`rounded-t-lg px-4 py-2 text-sm font-semibold transition ${
              tab === item.id
                ? 'border-b-2 border-brand-600 text-brand-700'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>

      {tab === 'sector' && <SectorComparisonView data={data} />}
      {tab === 'head' && <HeadToHeadCompare companiesByTicker={data?.companies_by_ticker} />}
      {tab === 'rankings' && <MarketRankings sectors={data?.sectors} />}
      {tab === 'score' && <InvestorScoreTable sectors={data?.sectors} />}
    </div>
  );
}
