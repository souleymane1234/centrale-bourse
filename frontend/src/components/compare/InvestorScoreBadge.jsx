import { formatNumber } from '../../utils/format';
import { recommendationLabel } from '../../utils/compareMetrics';

export default function InvestorScoreBadge({ score, recommendation, compact = false }) {
  const rec = recommendationLabel(recommendation);

  if (score == null) {
    return <span className="text-xs text-slate-400">Score N/A</span>;
  }

  if (compact) {
    return (
      <span className="inline-flex items-center gap-1.5">
        <span className="rounded-md bg-brand-50 px-1.5 py-0.5 text-xs font-bold text-brand-800">
          {formatNumber(score)}
        </span>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${rec.className}`}>
          {rec.label}
        </span>
      </span>
    );
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <span className="text-lg font-bold text-brand-800">{formatNumber(score)}/100</span>
      <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${rec.className}`}>
        {rec.label}
      </span>
    </div>
  );
}
