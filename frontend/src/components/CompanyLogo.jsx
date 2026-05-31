import { useMemo, useState } from 'react';
import { getCompanyLogoUrl } from '../utils/companyLogos';

function hashColor(value) {
  const input = String(value || 'BRVM');
  let hash = 0;
  for (let i = 0; i < input.length; i += 1) {
    hash = input.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue} 55% 42%)`;
}

export default function CompanyLogo({
  name,
  symbol,
  ticker,
  code,
  className = 'h-12 w-12',
}) {
  const [failed, setFailed] = useState(false);

  const localLogo = useMemo(
    () => getCompanyLogoUrl({ symbol, ticker, code }),
    [symbol, ticker, code]
  );

  const initials = useMemo(() => {
    const source = symbol || ticker || name || '?';
    const parts = source.trim().split(/\s+/).filter(Boolean);
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return source.slice(0, 2).toUpperCase();
  }, [name, symbol, ticker]);

  const bgColor = useMemo(() => hashColor(symbol || ticker || name), [symbol, ticker, name]);

  if (localLogo && !failed) {
    return (
      <img
        src={localLogo}
        alt=""
        loading="lazy"
        onError={() => setFailed(true)}
        className={`${className} shrink-0 rounded-lg border border-slate-100 bg-white object-contain p-1`}
      />
    );
  }

  return (
    <div
      className={`${className} flex shrink-0 items-center justify-center rounded-lg text-sm font-bold text-white`}
      style={{ backgroundColor: bgColor }}
      aria-hidden
    >
      {initials}
    </div>
  );
}
