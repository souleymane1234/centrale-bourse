import { Link } from 'react-router-dom';
import { companyPath } from '../../utils/routing';
import { formatText } from '../../utils/format';
import CompanyLogo from '../CompanyLogo';
import InvestorScoreBadge from './InvestorScoreBadge';

function SectorScoreBlock({ sector }) {
  const companies = [...(sector.companies || [])].sort(
    (a, b) => (b.investor_score ?? -1) - (a.investor_score ?? -1),
  );

  if (!companies.length) return null;

  return (
    <section className="card overflow-x-auto">
      <h3 className="text-base font-bold text-slate-900">{formatText(sector.sector)}</h3>
      <p className="mt-1 text-xs text-slate-500">
        Classement interne au secteur ({companies.length} société{companies.length > 1 ? 's' : ''})
      </p>
      <table className="mt-4 min-w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-slate-500">
            <th className="px-3 py-2 font-semibold">#</th>
            <th className="px-3 py-2 font-semibold">Société</th>
            <th className="px-3 py-2 font-semibold">Score & recommandation</th>
            <th className="px-3 py-2 font-semibold" />
          </tr>
        </thead>
        <tbody>
          {companies.map((company, index) => (
            <tr key={company.ticker} className="border-b border-slate-100">
              <td className="px-3 py-3 font-bold text-slate-400">{index + 1}</td>
              <td className="px-3 py-3">
                <div className="flex items-center gap-2">
                  <CompanyLogo
                    name={company.name}
                    symbol={company.symbol}
                    ticker={company.ticker}
                    code={company.code}
                    className="h-8 w-8"
                  />
                  <span className="font-medium text-slate-900">{formatText(company.name)}</span>
                </div>
              </td>
              <td className="px-3 py-3">
                <InvestorScoreBadge
                  score={company.investor_score}
                  recommendation={company.recommendation}
                />
              </td>
              <td className="px-3 py-3">
                <Link
                  to={companyPath(company.ticker)}
                  className="font-semibold text-brand-700 hover:underline"
                >
                  Fiche
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export default function InvestorScoreTable({ sectors }) {
  const sectorList = (sectors || []).filter((sector) => (sector.companies || []).length > 0);

  return (
    <div className="space-y-4">
      <section className="card">
        <h2 className="text-xl font-bold text-slate-900">Score investisseur</h2>
        <p className="mt-2 text-sm text-slate-600">
          Note synthétique sur 100 par rapport aux pairs du même secteur (rentabilité, croissance,
          dividendes, valorisation, marché). Le classement ci-dessous est établi secteur par secteur.
        </p>
        <ul className="mt-3 list-inside list-disc text-xs text-slate-500">
          <li>Rentabilité — 25 %</li>
          <li>Croissance — 20 %</li>
          <li>Dividendes — 20 %</li>
          <li>Valorisation — 15 %</li>
          <li>Marché — 20 %</li>
        </ul>
      </section>

      {sectorList.map((sector) => (
        <SectorScoreBlock key={sector.sector} sector={sector} />
      ))}
    </div>
  );
}
