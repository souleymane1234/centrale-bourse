import { Fragment } from 'react';
import { Link } from 'react-router-dom';
import { companyPath } from '../../utils/routing';
import { formatText } from '../../utils/format';
import {
  COMPARE_MATRIX_SECTIONS,
  formatMatrixValue,
  getMatrixCellValue,
  peerRankTone,
  pickRowWinner,
} from '../../utils/compareMatrix';

function MatrixCell({ company, row, peersValues }) {
  const value = getMatrixCellValue(company, row.key);
  const display = formatMatrixValue(value, row.format);
  const rank = peerRankTone(value, peersValues, row.higherBetter);

  const textClass =
    rank === 'best'
      ? 'font-semibold text-emerald-600'
      : rank === 'worst'
        ? 'font-semibold text-rose-600'
        : 'text-slate-800';

  return (
    <td className="border-b border-slate-100 px-3 py-2.5 text-center text-sm tabular-nums">
      <span className={textClass}>{display}</span>
    </td>
  );
}

export default function ComparisonMatrixTable({
  companies,
  highlightWinner = false,
  minWidth = '640px',
}) {
  if (!companies?.length) {
    return <p className="text-sm text-slate-500">Sélectionnez des sociétés à comparer.</p>;
  }

  const sorted = [...companies].sort((a, b) =>
    (a.symbol || a.ticker || '').localeCompare(b.symbol || b.ticker || ''),
  );

  const showWinnerColumn = highlightWinner && sorted.length === 2;
  const colSpan = sorted.length + 1 + (showWinnerColumn ? 1 : 0);

  return (
    <div className="overflow-x-auto overscroll-x-contain rounded-lg border border-slate-200">
      <table className="w-full border-collapse text-sm" style={{ minWidth }}>
        <thead>
          <tr className="border-b border-slate-200 bg-white">
            <th className="sticky left-0 z-20 min-w-[200px] bg-white px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500">
              KPI
            </th>
            {sorted.map((company) => (
              <th
                key={company.ticker}
                className="min-w-[100px] border-l border-slate-100 px-2 py-3 text-center"
              >
                <Link
                  to={companyPath(company.ticker)}
                  className="text-sm font-bold tracking-wide text-slate-900 hover:text-brand-700"
                  title={formatText(company.name)}
                >
                  {formatText(company.symbol || company.ticker)}
                </Link>
                {highlightWinner && (
                  <p className="mt-0.5 truncate text-[10px] font-normal text-slate-500">
                    {formatText(company.name)}
                  </p>
                )}
              </th>
            ))}
            {showWinnerColumn && (
              <th className="min-w-[72px] border-l border-slate-100 px-2 py-3 text-center text-xs font-bold uppercase tracking-wide text-slate-500">
                Gagnant
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {COMPARE_MATRIX_SECTIONS.map((section) => (
            <Fragment key={section.id}>
              <tr className="bg-sky-50/90">
                <td
                  colSpan={colSpan}
                  className="sticky left-0 px-4 py-2 text-xs font-bold uppercase tracking-wide text-slate-700"
                >
                  <span className="mr-2" aria-hidden>
                    {section.icon}
                  </span>
                  {section.title}
                </td>
              </tr>
              {section.rows.map((row, rowIndex) => {
                const peersValues = sorted.map((c) => getMatrixCellValue(c, row.key));
                const winnerTicker = showWinnerColumn ? pickRowWinner(sorted, row) : null;
                const winnerCompany = sorted.find((c) => c.ticker === winnerTicker);

                return (
                  <tr
                    key={`${section.id}-${row.key}`}
                    className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-slate-50/60'}
                  >
                    <th
                      scope="row"
                      className={`sticky left-0 z-10 border-b border-slate-100 px-4 py-2.5 text-left text-xs font-medium text-slate-600 ${
                        rowIndex % 2 === 0 ? 'bg-white' : 'bg-slate-50'
                      }`}
                    >
                      <span className="border-b border-dotted border-slate-300">{row.label}</span>
                    </th>
                    {sorted.map((company) => (
                      <MatrixCell
                        key={`${company.ticker}-${row.key}`}
                        company={company}
                        row={row}
                        peersValues={peersValues}
                      />
                    ))}
                    {showWinnerColumn && (
                      <td className="border-b border-slate-100 border-l border-slate-100 px-2 py-2.5 text-center text-xs font-semibold text-emerald-600">
                        {winnerCompany
                          ? formatText(winnerCompany.symbol || winnerCompany.ticker)
                          : '—'}
                      </td>
                    )}
                  </tr>
                );
              })}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
