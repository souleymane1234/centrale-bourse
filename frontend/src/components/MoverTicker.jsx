import { formatNumber, formatPercent } from '../utils/format';

function TickerItem({ item, onSelect }) {
  const variation = item.variation ?? 0;
  const isUp = variation > 0;
  const isDown = variation < 0;

  const arrowColor = isUp ? 'text-emerald-400' : isDown ? 'text-rose-400' : 'text-slate-400';
  const percentColor = isUp ? 'text-emerald-300' : isDown ? 'text-rose-300' : 'text-white';

  const arrow = isUp ? '▲' : isDown ? '▼' : '•';
  const symbol = item.symbol || item.ticker || '—';

  const Tag = onSelect ? 'button' : 'span';

  return (
    <Tag
      type={onSelect ? 'button' : undefined}
      onClick={onSelect ? () => onSelect(item) : undefined}
      className={`inline-flex shrink-0 items-center gap-2 px-4 text-sm text-white ${
        onSelect ? 'cursor-pointer rounded hover:bg-white/10' : ''
      }`}
    >
      <span className="font-bold tracking-wide">{symbol}</span>
      <span className="tabular-nums">{formatNumber(item.price)}</span>
      <span className={`tabular-nums font-semibold ${percentColor}`}>{formatPercent(variation)}</span>
      <span className={`text-xs ${arrowColor}`} aria-hidden>
        {arrow}
      </span>
      <span className="text-slate-500">|</span>
    </Tag>
  );
}

export default function MoverTicker({
  label,
  items,
  badgeClassName,
  duration = 50,
  onSelectItem,
}) {
  if (!items?.length) {
    return (
      <div className="flex overflow-hidden rounded-md">
        <div className={`shrink-0 px-4 py-2.5 text-sm font-bold text-white ${badgeClassName}`}>
          {label}
        </div>
        <div className="flex flex-1 items-center bg-[#1e3a6e] px-4 py-2.5 text-sm text-slate-300">
          Aucune donnée disponible
        </div>
      </div>
    );
  }

  const loop = [...items, ...items];

  return (
    <div className="flex overflow-hidden rounded-md shadow-sm">
      <div
        className={`flex shrink-0 items-center px-4 py-2.5 text-sm font-bold uppercase tracking-wide text-white ${badgeClassName}`}
      >
        {label}
      </div>
      <div className="relative min-w-0 flex-1 overflow-hidden bg-[#1e3a6e]">
        <div
          className="ticker-track flex w-max items-center py-2.5"
          style={{ animationDuration: `${duration}s` }}
        >
          {loop.map((item, index) => (
            <TickerItem
              key={`${item.symbol || item.ticker}-${item.variation}-${index}`}
              item={item}
              onSelect={onSelectItem}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
