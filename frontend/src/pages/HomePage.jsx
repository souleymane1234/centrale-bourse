import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchHome } from '../api/client';
import MarketSummary from '../components/MarketSummary';
import MoverTicker from '../components/MoverTicker';
import CompanyToolbar from '../components/CompanyToolbar';
import CompanyCardsGrid from '../components/CompanyCardsGrid';
import Spinner from '../components/Spinner';
import { companyPath, resolveCompanyTicker } from '../utils/routing';

export default function HomePage() {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState([]);
  const [marketSummary, setMarketSummary] = useState(null);
  const [sectorFilter, setSectorFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadHome = async ({ showSpinner = true } = {}) => {
    if (showSpinner) {
      setLoading(true);
    }
    setError(null);
    try {
      const home = await fetchHome();
      setCompanies(home.companies || []);
      setMarketSummary(home.market_summary || null);
    } catch (err) {
      setError(
        err.message ||
          "Impossible de charger les données. Démarrez Flask (port 5050) puis lancez npm run dev dans frontend/."
      );
    } finally {
      if (showSpinner) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    loadHome();
  }, []);

  const sectors = useMemo(
    () => [...new Set(companies.map((c) => c.sector).filter(Boolean))].sort(),
    [companies]
  );

  const topGainers = useMemo(() => {
    if (marketSummary?.top_gainers?.length) {
      return marketSummary.top_gainers;
    }
    return [...companies]
      .filter((c) => (c.variation ?? 0) > 0)
      .sort((a, b) => (b.variation ?? 0) - (a.variation ?? 0))
      .slice(0, 30);
  }, [marketSummary, companies]);

  const topLosers = useMemo(() => {
    if (marketSummary?.top_losers?.length) {
      return marketSummary.top_losers;
    }
    return [...companies]
      .filter((c) => (c.variation ?? 0) < 0)
      .sort((a, b) => (a.variation ?? 0) - (b.variation ?? 0))
      .slice(0, 30);
  }, [marketSummary, companies]);

  const palmaresItems = useMemo(
    () => [...topGainers, ...topLosers],
    [topGainers, topLosers]
  );

  const filteredCompanies = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return companies.filter((company) => {
      const matchesSector = !sectorFilter || company.sector === sectorFilter;
      const haystack = [company.name, company.symbol, company.ticker, company.sector]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      const matchesQuery = !query || haystack.includes(query);
      return matchesSector && matchesQuery;
    });
  }, [companies, sectorFilter, searchQuery]);

  const handleCompanySelect = (ticker) => {
    navigate(companyPath(ticker));
  };

  const handleMoverSelect = (item) => {
    const ticker = item.ticker || item.symbol;
    if (!ticker) return;
    const resolved = resolveCompanyTicker(ticker, companies);
    if (resolved) {
      navigate(companyPath(resolved));
    }
  };

  if (loading) {
    return <Spinner label="Chargement du dashboard..." />;
  }

  return (
    <div className="mx-auto max-w-7xl space-y-5 px-4 py-6 sm:px-6">
      <div className="-mx-4 sm:-mx-6">
        <MoverTicker
          label="Palmarès BRVM"
          items={palmaresItems}
          badgeClassName="bg-[#1e3a6e] ring-1 ring-inset ring-white/20"
          duration={99}
          onSelectItem={handleMoverSelect}
        />
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {error}
        </div>
      )}

      <MarketSummary summary={marketSummary} />

      <CompanyToolbar
        sectors={sectors}
        sectorFilter={sectorFilter}
        searchQuery={searchQuery}
        onSectorChange={setSectorFilter}
        onSearchChange={setSearchQuery}
        onRefresh={() => loadHome({ showSpinner: false })}
      />

      <CompanyCardsGrid companies={filteredCompanies} onSelect={handleCompanySelect} />
    </div>
  );
}
