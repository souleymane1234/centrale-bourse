import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  fetchAnalysis,
  fetchCompanies,
  peekAnalysisCache,
  peekCompaniesCache,
  refreshAnalysis,
} from '../api/client';
import AnalysisDashboard from '../components/AnalysisDashboard';
import Spinner from '../components/Spinner';
import { companyPath, normalizeTicker, resolveCompanyTicker } from '../utils/routing';

export default function CompanyPage() {
  const { ticker: tickerParam } = useParams();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState(() => peekCompaniesCache() || []);
  const [analysis, setAnalysis] = useState(() =>
    tickerParam ? peekAnalysisCache(tickerParam) : null
  );
  const [loading, setLoading] = useState(() => !peekCompaniesCache());
  const [analysisLoading, setAnalysisLoading] = useState(
    () => !(tickerParam && peekAnalysisCache(tickerParam))
  );
  const [error, setError] = useState(null);

  const activeTicker = useMemo(() => {
    if (!tickerParam || !companies.length) return '';
    return resolveCompanyTicker(tickerParam, companies) || '';
  }, [tickerParam, companies]);

  const loadAnalysis = useCallback(async (ticker) => {
    if (!ticker) return;

    const cached = peekAnalysisCache(ticker);
    if (cached) {
      setAnalysis(cached);
      setAnalysisLoading(false);
    } else {
      setAnalysisLoading(true);
    }

    setError(null);
    try {
      const data = await fetchAnalysis(ticker, { force: Boolean(cached) });
      setAnalysis(data);
    } catch (err) {
      if (!cached) {
        setError(err.message);
        setAnalysis(null);
      }
    } finally {
      setAnalysisLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      const cached = peekCompaniesCache();
      if (!cached) {
        setLoading(true);
      }

      try {
        const companyList = await fetchCompanies({ force: Boolean(cached) });
        if (!cancelled) {
          setCompanies(companyList);
        }
      } catch (err) {
        if (!cancelled && !cached) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (loading || !companies.length || !tickerParam) return;

    const resolved = resolveCompanyTicker(tickerParam, companies);
    if (!resolved) {
      setError(`Société introuvable : « ${tickerParam} »`);
      setAnalysis(null);
      return;
    }

    if (normalizeTicker(tickerParam) !== normalizeTicker(resolved)) {
      navigate(companyPath(resolved), { replace: true });
      return;
    }

    loadAnalysis(resolved);
  }, [loading, companies, tickerParam, navigate, loadAnalysis]);

  const handleRefresh = async () => {
    if (!activeTicker) return;
    setAnalysisLoading(true);
    setError(null);
    try {
      const data = await refreshAnalysis(activeTicker);
      setAnalysis(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalysisLoading(false);
    }
  };

  if (loading && !companies.length) {
    return <Spinner label="Chargement de la société..." />;
  }

  const showAnalysisSpinner = analysisLoading && !analysis;

  return (
    <div className="mx-auto max-w-7xl space-y-5 overflow-x-hidden px-4 py-6 sm:px-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-sm font-semibold text-brand-700 hover:text-brand-800"
        >
          ← Retour à la liste
        </Link>

        <button
          type="button"
          onClick={handleRefresh}
          disabled={!activeTicker || analysisLoading}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
        >
          Actualiser
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {error}
        </div>
      )}

      {showAnalysisSpinner && <Spinner label="Analyse en cours..." />}
      {analysis && (
        <div className={analysisLoading ? 'opacity-80 transition-opacity' : undefined}>
          <AnalysisDashboard analysis={analysis} />
        </div>
      )}
    </div>
  );
}
