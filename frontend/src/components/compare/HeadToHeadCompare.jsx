import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { companyPath } from '../../utils/routing';
import { countHeadToHeadWins } from '../../utils/compareMatrix';
import { formatText } from '../../utils/format';
import ComparisonMatrixTable from './ComparisonMatrixTable';
import InvestorScoreBadge from './InvestorScoreBadge';

const UNKNOWN_SECTOR = 'Non classé';

export default function HeadToHeadCompare({ companiesByTicker }) {
  const companiesList = useMemo(
    () => Object.values(companiesByTicker || {}),
    [companiesByTicker],
  );

  const sectors = useMemo(() => {
    const names = new Set(companiesList.map((c) => c.sector || UNKNOWN_SECTOR));
    return [...names].sort((a, b) => a.localeCompare(b, 'fr'));
  }, [companiesList]);

  const [sector, setSector] = useState('');
  const [leftTicker, setLeftTicker] = useState('');
  const [rightTicker, setRightTicker] = useState('');

  useEffect(() => {
    if (!sector && sectors.length) setSector(sectors[0]);
  }, [sectors, sector]);

  const sectorCompanies = useMemo(() => {
    const active = sector || sectors[0] || UNKNOWN_SECTOR;
    return companiesList
      .filter((c) => (c.sector || UNKNOWN_SECTOR) === active)
      .sort((a, b) =>
        (a.symbol || a.ticker || '').localeCompare(b.symbol || b.ticker || '', 'fr'),
      );
  }, [companiesList, sector, sectors]);

  const tickers = useMemo(() => sectorCompanies.map((c) => c.ticker), [sectorCompanies]);

  useEffect(() => {
    if (!tickers.length) {
      setLeftTicker('');
      setRightTicker('');
      return;
    }
    setLeftTicker((prev) => (tickers.includes(prev) ? prev : tickers[0]));
    setRightTicker((prev) => {
      if (tickers.includes(prev) && prev !== tickers[0]) return prev;
      return tickers.length >= 2 ? tickers[1] : '';
    });
  }, [sector, tickers.join('|')]);

  const leftProfile = companiesByTicker?.[leftTicker];
  const rightProfile = companiesByTicker?.[rightTicker];
  const canCompare =
    leftProfile &&
    rightProfile &&
    leftTicker !== rightTicker &&
    (leftProfile.sector || UNKNOWN_SECTOR) === (rightProfile.sector || UNKNOWN_SECTOR);

  const pair = useMemo(
    () => (canCompare ? [leftProfile, rightProfile] : []),
    [canCompare, leftProfile, rightProfile],
  );

  const { leftWins, rightWins } = useMemo(() => countHeadToHeadWins(pair), [pair]);

  return (
    <div className="space-y-6">
      <section className="card">
        <h2 className="text-xl font-bold text-slate-900">Comparer 2 entreprises</h2>
        <p className="mt-2 text-sm text-slate-600">
          Choisissez d’abord un secteur, puis deux sociétés de ce secteur. Les KPI et le score
          investisseur sont calculés par rapport aux pairs du même secteur.
        </p>

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <label className="block text-sm sm:col-span-3 md:col-span-1">
            <span className="mb-1 block font-medium text-slate-700">Secteur</span>
            <select
              value={sector}
              onChange={(e) => setSector(e.target.value)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
            >
              {sectors.map((name) => (
                <option key={name} value={name}>
                  {formatText(name)} ({companiesList.filter((c) => (c.sector || UNKNOWN_SECTOR) === name).length})
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Entreprise A</span>
            <select
              value={leftTicker}
              onChange={(e) => setLeftTicker(e.target.value)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
              disabled={tickers.length < 1}
            >
              {sectorCompanies.map((company) => (
                <option
                  key={company.ticker}
                  value={company.ticker}
                  disabled={company.ticker === rightTicker}
                >
                  {formatText(company.symbol || company.ticker)} — {formatText(company.name)}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Entreprise B</span>
            <select
              value={rightTicker}
              onChange={(e) => setRightTicker(e.target.value)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
              disabled={tickers.length < 2}
            >
              {sectorCompanies.map((company) => (
                <option
                  key={company.ticker}
                  value={company.ticker}
                  disabled={company.ticker === leftTicker}
                >
                  {formatText(company.symbol || company.ticker)} — {formatText(company.name)}
                </option>
              ))}
            </select>
          </label>
        </div>

        {tickers.length < 2 && (
          <p className="mt-3 text-sm text-amber-700">
            Ce secteur ne compte qu’une société cotée : la comparaison face-à-face nécessite au moins
            deux entreprises.
          </p>
        )}
      </section>

      {canCompare && (
        <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-card">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-4 py-3">
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <span>
                <Link
                  to={companyPath(leftProfile.ticker)}
                  className="font-bold text-slate-900 hover:text-brand-700"
                >
                  {formatText(leftProfile.symbol)}
                </Link>
                : {leftWins} critère{leftWins > 1 ? 's' : ''}
              </span>
              <span className="text-slate-300">·</span>
              <span>
                <Link
                  to={companyPath(rightProfile.ticker)}
                  className="font-bold text-slate-900 hover:text-brand-700"
                >
                  {formatText(rightProfile.symbol)}
                </Link>
                : {rightWins} critère{rightWins > 1 ? 's' : ''}
              </span>
            </div>
            <div className="flex flex-wrap gap-4">
              <InvestorScoreBadge
                score={leftProfile.investor_score}
                recommendation={leftProfile.recommendation}
                compact
              />
              <InvestorScoreBadge
                score={rightProfile.investor_score}
                recommendation={rightProfile.recommendation}
                compact
              />
            </div>
          </div>
          <div className="p-4">
            <ComparisonMatrixTable companies={pair} highlightWinner minWidth="480px" />
          </div>
        </section>
      )}

      {leftTicker && rightTicker && leftTicker === rightTicker && (
        <p className="text-center text-sm text-slate-500">
          Choisissez deux sociétés différentes pour lancer la comparaison.
        </p>
      )}
    </div>
  );
}
