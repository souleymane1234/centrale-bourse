const API_BASE = import.meta.env.DEV ? '' : '';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Erreur API (${response.status})`);
  }
  return data;
}

export function fetchCompanies() {
  return request('/api/companies');
}

/** Accueil : sociétés + résumé marché (1 requête, cache serveur). */
export function fetchHome() {
  return request('/api/home');
}

export function fetchCompareBySector() {
  return request('/api/compare/by-sector');
}

export function fetchCompareHeadToHead(tickerA, tickerB) {
  const params = new URLSearchParams({ tickers: tickerA });
  params.append('tickers', tickerB);
  return request(`/api/compare/head-to-head?${params.toString()}`);
}

export function fetchMarketSummary() {
  return request('/api/market-summary');
}

export function fetchAnalysis(ticker) {
  return request(`/api/analysis/${ticker}`);
}

export function refreshAnalysis(ticker) {
  return request(`/api/refresh/${ticker}`);
}

export function fetchNews(page = 1, perPage = 12) {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
  });
  return request(`/api/news?${params.toString()}`);
}

export function fetchNewsArticle(slug) {
  return request(`/api/news/${encodeURIComponent(slug)}`);
}
