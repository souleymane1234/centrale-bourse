import { Maximize2 } from 'lucide-react';
import CompanyFollowActions from './follow/CompanyFollowActions';
import PriceChart from './PriceChart';
import FinancialMetricChart from './FinancialMetricChart';
import FinancialStatementsSection from './FinancialStatementsSection';
import TechnicalAnalysisCharts from './TechnicalAnalysisCharts';
import CompanyLogo from './CompanyLogo';
import {
  formatCurrency,
  formatNumber,
  formatPercent,
  formatShares,
  formatMarketCapMfcfa,
  formatText,
  formatDateTime,
  variationBadgeClass,
} from '../utils/format';
import {
  computePreviousClose,
  displaySymbol,
  formatIndustryLabel,
  formatWebsiteDisplay,
  parseChiefExecutiveFromRaw,
  parseChairmanFromRaw,
  isValidExecutiveName,
} from '../utils/companyProfile';

function MetricCell({ label, value }) {
  return (
    <div className="min-w-[4.5rem] shrink-0">
      <div className="text-[11px] font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-0.5 text-sm font-semibold text-slate-800">{value}</div>
    </div>
  );
}

function ProfileField({ label, value, href }) {
  const content = href ? (
    <a
      href={href.startsWith('http') ? href : `https://${href}`}
      target="_blank"
      rel="noopener noreferrer"
      className="font-medium text-slate-900 underline decoration-slate-300 underline-offset-2 hover:text-brand-700"
    >
      {value}
    </a>
  ) : (
    <span className="font-medium text-slate-900">{value}</span>
  );

  return (
    <div>
      <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-sm">{content}</div>
    </div>
  );
}

function DataTable({ headers, rows }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-slate-500">
            {headers.map((header) => (
              <th key={header} className="px-2 py-2 font-semibold">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-b border-slate-100">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-2 py-2 text-slate-800">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function AnalysisDashboard({ analysis }) {
  const company = analysis.company || {};
  const quote = analysis.market_quote || company.market_quote || {};
  const technical = analysis.technical || {};
  const fundamental = analysis.fundamental || {};
  const ratios = fundamental.ratios || {};

  const symbol = displaySymbol(company, quote);
  const variation = quote.variation_pct ?? null;
  const previousClose = quote.previous_close ?? computePreviousClose(quote);
  const price = quote.last ?? analysis.current_price;
  const industry = formatIndustryLabel(company.sector);
  const website = company.website;
  const websiteLabel = formatWebsiteDisplay(website);

  const governanceRaw =
    company.governance_raw ||
    company.sikafinance_governance?.raw ||
    null;
  const rawChief =
    company.chief_executive || parseChiefExecutiveFromRaw(governanceRaw) || null;
  const chiefExecutive = isValidExecutiveName(rawChief) ? rawChief : null;
  const rawChairman = company.chairman || parseChairmanFromRaw(governanceRaw) || null;
  const chairman = isValidExecutiveName(rawChairman) ? rawChairman : null;
  const executiveLabel =
    chiefExecutive && /président\s+directeur|pdg\b/i.test(governanceRaw || '')
      ? 'PDG'
      : 'Directeur général';

  const profileSummary = company.profile_summary || null;
  const updatedAt = analysis.last_updated || analysis.dataset_generated_at;

  const boardMembers = (company.board_members || []).slice(0, 6);
  const showBoardStructure = boardMembers.some(
    (member) => member.structure && !/^sikafinance$/i.test(String(member.structure).trim())
  );
  const boardRows = boardMembers.map((member) =>
    showBoardStructure
      ? [formatText(member.name), formatText(member.role), formatText(member.structure)]
      : [formatText(member.name), formatText(member.role)]
  );

  const shareholding = company.shareholding || {};
  const shareholderRows = (shareholding.shareholders || []).map((holder) => [
    formatText(holder.name),
    holder.percentage != null ? formatPercent(holder.percentage) : formatText(holder.raw_percentage),
  ]);

  const financials = analysis.financials || {};
  const marketStats = company.market_stats || financials.market_stats || null;
  const statements = (
    company.financial_statements?.length
      ? company.financial_statements
      : financials.statements
  ) || [];

  const revenueChart = financials.chart?.revenue || [];
  const netIncomeChart = financials.chart?.net_income || [];

  return (
    <div className="min-w-0 space-y-6 overflow-x-hidden">
      {/* Hero — cotations + profil (maquette) */}
      <section className="overflow-hidden rounded-2xl border border-slate-200/90 bg-[#e8f0f5] shadow-card">
        <div className="grid lg:grid-cols-[1fr_300px]">
          <div className="p-5 sm:p-6 lg:p-8">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-4">
                <CompanyLogo
                  name={company.name}
                  symbol={symbol}
                  ticker={analysis.ticker}
                  code={quote.code}
                  className="h-14 w-14 sm:h-16 sm:w-16"
                />
                <div>
                  <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
                    {formatText(company.name)}
                  </h1>
                  <p className="mt-0.5 text-sm font-medium text-slate-600">
                    {formatText(symbol)} | BRVM
                  </p>
                </div>
              </div>
              <CompanyFollowActions
                ticker={analysis.ticker}
                companyName={company.name}
                currentPrice={price}
              />
            </div>

            <div className="mt-6 flex flex-wrap items-end gap-3">
              <div className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
                {formatCurrency(price)}
              </div>
              {variation != null && (
                <span
                  className={`mb-1 inline-flex rounded-full px-3 py-1 text-sm font-semibold ${variationBadgeClass(variation)}`}
                >
                  {variation > 0 ? '+' : ''}
                  {formatPercent(variation)} aujourd&apos;hui
                </span>
              )}
            </div>

            <div className="mt-5 flex flex-wrap gap-x-6 gap-y-3 border-b border-slate-200/70 pb-5">
              <MetricCell label="Préc." value={formatCurrency(previousClose)} />
              <MetricCell label="Ouv." value={formatCurrency(quote.opening)} />
              <MetricCell label="Élevé" value={formatCurrency(quote.high)} />
              <MetricCell label="Bas" value={formatCurrency(quote.low)} />
              <MetricCell label="Vol." value={formatNumber(quote.volume_shares)} />
              <MetricCell label="Mise à jour" value={formatDateTime(updatedAt)} />
            </div>

            <div className="relative mt-4">
              <button
                type="button"
                className="absolute right-0 top-0 z-10 rounded-lg p-1.5 text-slate-400 hover:bg-white/70 hover:text-slate-600"
                aria-label="Graphique plein écran (bientôt disponible)"
                title="Plein écran — bientôt disponible"
              >
                <Maximize2 className="h-4 w-4" strokeWidth={1.75} />
              </button>
              <PriceChart historicalPrices={analysis.historical_prices} className="h-72 sm:h-80" />
            </div>
          </div>

          <aside className="border-t border-slate-200/80 bg-white/70 p-5 sm:p-6 lg:border-l lg:border-t-0">
            <h2 className="text-[11px] font-bold uppercase tracking-widest text-slate-500">
              Profil de l&apos;entreprise
            </h2>

            <div className="mt-5 space-y-5">
              {chiefExecutive && (
                <ProfileField label={executiveLabel} value={chiefExecutive} />
              )}
              {!chiefExecutive && chairman && (
                <ProfileField label="Président du CA" value={chairman} />
              )}
              {websiteLabel && (
                <ProfileField
                  label="Site Web"
                  value={websiteLabel}
                  href={website}
                />
              )}
              {industry && <ProfileField label="Industrie" value={industry} />}
              {company.listing_date && (
                <ProfileField label="Listé depuis" value={formatText(company.listing_date)} />
              )}
            </div>

            {profileSummary && (
              <p className="mt-6 text-sm leading-relaxed text-slate-600">{profileSummary}</p>
            )}

            {!profileSummary && !chiefExecutive && !industry && (
              <p className="mt-6 text-sm text-slate-500">
                Profil détaillé en cours d&apos;enrichissement via le scraping BRVM.
              </p>
            )}
          </aside>
        </div>
      </section>

      <TechnicalAnalysisCharts
        series={analysis.technical_series}
        latest={technical}
      />

      {(marketStats || statements.length > 0) && (
        <section className="grid min-w-0 gap-4 xl:grid-cols-2">
          {marketStats && (
            <div className="card min-w-0">
              <h3 className="mb-3 text-lg font-bold">Structure du capital</h3>
              <div className="space-y-0">
                <div className="flex justify-between gap-3 border-b border-slate-100 py-2">
                  <span className="text-sm text-slate-500">Nombre de titres</span>
                  <span className="text-sm font-semibold">
                    {formatShares(marketStats.shares_outstanding)}
                  </span>
                </div>
                <div className="flex justify-between gap-3 border-b border-slate-100 py-2">
                  <span className="text-sm text-slate-500">Flottant</span>
                  <span className="text-sm font-semibold">
                    {formatPercent(marketStats.float_pct)}
                  </span>
                </div>
                <div className="flex justify-between gap-3 border-b border-slate-100 py-2">
                  <span className="text-sm text-slate-500">Valorisation</span>
                  <span className="text-sm font-semibold">
                    {formatMarketCapMfcfa(marketStats.market_cap_mfcfa)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {statements.length > 0 && (
            <div className={`card min-w-0 overflow-hidden ${marketStats ? '' : 'xl:col-span-2'}`}>
              <h3 className="mb-3 text-lg font-bold">Indicateurs financiers (5 ans)</h3>
              <p className="mb-3 text-xs text-slate-500">
                Chiffres en millions.
              </p>
              <FinancialStatementsSection statements={statements} />
            </div>
          )}
        </section>
      )}

      {(revenueChart.length > 0 || netIncomeChart.length > 0) && (
        <section className="grid gap-4 xl:grid-cols-2">
          <div className="card">
            <h3 className="mb-3 text-lg font-bold">Évolution du chiffre d&apos;affaires</h3>
            <FinancialMetricChart
              series={revenueChart}
              valueLabel="M FCFA"
              color="#3b82f6"
              className="h-64"
            />
          </div>
          <div className="card">
            <h3 className="mb-3 text-lg font-bold">Évolution du résultat net</h3>
            <FinancialMetricChart
              series={netIncomeChart}
              valueLabel="M FCFA"
              color="#10b981"
              className="h-64"
            />
          </div>
        </section>
      )}

      <section className="grid gap-4 xl:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 text-lg font-bold">Société</h3>
          <div className="space-y-0">
            <div className="flex justify-between gap-3 border-b border-slate-100 py-2">
              <span className="text-sm text-slate-500">Raison sociale</span>
              <span className="text-sm font-semibold">{formatText(company.legal_name)}</span>
            </div>
            <div className="flex justify-between gap-3 border-b border-slate-100 py-2">
              <span className="text-sm text-slate-500">Capital social</span>
              <span className="text-sm font-semibold">{formatText(company.capital_social)}</span>
            </div>
            <div className="flex justify-between gap-3 border-b border-slate-100 py-2">
              <span className="text-sm text-slate-500">Adresse</span>
              <span className="text-sm font-semibold text-right">{formatText(company.address)}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="mb-3 text-lg font-bold">Fondamental</h3>
          <div className="space-y-0">
            <div className="flex justify-between gap-3 border-b border-slate-100 py-2">
              <span className="text-sm text-slate-500">Chiffre d&apos;affaires</span>
              <span className="text-sm font-semibold">{formatNumber(fundamental.revenue)} Md FCFA</span>
            </div>
            <div className="flex justify-between gap-3 border-b border-slate-100 py-2">
              <span className="text-sm text-slate-500">Résultat net</span>
              <span className="text-sm font-semibold">{formatNumber(fundamental.net_income)} Md FCFA</span>
            </div>
            <div className="flex justify-between gap-3 border-b border-slate-100 py-2">
              <span className="text-sm text-slate-500">PER</span>
              <span className="text-sm font-semibold">{formatNumber(fundamental.pe_ratio)}</span>
            </div>
            <div className="flex justify-between gap-3 border-b border-slate-100 py-2">
              <span className="text-sm text-slate-500">ROE</span>
              <span className="text-sm font-semibold">{formatPercent(ratios.roe)}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="mb-3 text-lg font-bold">Gouvernance</h3>
          {company.governance_is_stale && (
            <p className="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
              {formatText(company.governance_note)}
            </p>
          )}
          {boardRows.length > 0 ? (
            <DataTable
              headers={showBoardStructure ? ['Nom', 'Fonction', 'Structure'] : ['Nom', 'Fonction']}
              rows={boardRows}
            />
          ) : (
            <p className="text-sm text-slate-500">Aucune donnée de gouvernance structurée.</p>
          )}
        </div>

        <div className="card">
          <h3 className="mb-3 text-lg font-bold">Actionnariat</h3>
          {shareholding.total_shares != null && (
            <p className="mb-3 text-sm text-slate-600">
              <span className="text-slate-500">Nombre de titres : </span>
              <span className="font-semibold text-slate-800">
                {formatShares(shareholding.total_shares)}
              </span>
            </p>
          )}
          {shareholderRows.length > 0 ? (
            <DataTable headers={['Actionnaire', 'Part']} rows={shareholderRows} />
          ) : (
            <p className="text-sm text-slate-500">Aucune donnée d&apos;actionnariat disponible.</p>
          )}
        </div>

      </section>
    </div>
  );
}
