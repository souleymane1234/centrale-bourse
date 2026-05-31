/** Normalise un identifiant ticker/symbole pour comparaison. */
export function normalizeTicker(value) {
  if (!value) return '';
  return String(value).toUpperCase().replace(/[^A-Z0-9]/g, '');
}

/**
 * Retrouve le ticker interne à partir du paramètre d'URL (/societe/SONATEL).
 */
export function resolveCompanyTicker(param, companies) {
  if (!param || !companies?.length) return null;

  const needle = normalizeTicker(param);
  if (!needle) return null;

  for (const company of companies) {
    const candidates = [company.ticker, company.symbol, company.name]
      .filter(Boolean)
      .map(normalizeTicker);

    if (candidates.includes(needle)) {
      return company.ticker;
    }
  }

  // Correspondance partielle sur le nom (ex. "sonatel" → SONATEL)
  const byName = companies.find((company) => {
    const name = normalizeTicker(company.name);
    return name.includes(needle) || needle.includes(name);
  });

  return byName?.ticker ?? null;
}

export function companyPath(ticker) {
  return `/societe/${encodeURIComponent(ticker)}`;
}
