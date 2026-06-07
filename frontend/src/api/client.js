import { apiUrl } from '../config/api';
import { deleteCache, readCache, writeCache } from './memoryCache';
import { normalizeTicker } from '../utils/routing';

const COMPANIES_CACHE_KEY = 'companies';
const ANALYSIS_CACHE_PREFIX = 'analysis:';
const COMPANIES_TTL_MS = 10 * 60 * 1000;
const ANALYSIS_TTL_MS = 10 * 60 * 1000;

async function request(path, options = {}) {
  const response = await fetch(apiUrl(path), options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Erreur API (${response.status})`);
  }
  return data;
}

export function peekCompaniesCache() {
  return readCache(COMPANIES_CACHE_KEY);
}

export function seedCompaniesCache(companies) {
  if (Array.isArray(companies) && companies.length) {
    writeCache(COMPANIES_CACHE_KEY, companies, COMPANIES_TTL_MS);
  }
}

export function peekAnalysisCache(ticker) {
  const key = `${ANALYSIS_CACHE_PREFIX}${normalizeTicker(ticker)}`;
  return readCache(key);
}

export function invalidateAnalysisCache(ticker) {
  const key = `${ANALYSIS_CACHE_PREFIX}${normalizeTicker(ticker)}`;
  deleteCache(key);
}

export async function fetchCompanies({ force = false } = {}) {
  if (!force) {
    const cached = readCache(COMPANIES_CACHE_KEY);
    if (cached) {
      return cached;
    }
  }

  const data = await request('/api/companies');
  writeCache(COMPANIES_CACHE_KEY, data, COMPANIES_TTL_MS);
  return data;
}

export async function fetchHome() {
  const data = await request('/api/home');
  if (Array.isArray(data.companies)) {
    seedCompaniesCache(data.companies);
  }
  return data;
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

export async function fetchAnalysis(ticker, { force = false } = {}) {
  const cacheKey = `${ANALYSIS_CACHE_PREFIX}${normalizeTicker(ticker)}`;
  if (!force) {
    const cached = readCache(cacheKey);
    if (cached) {
      return cached;
    }
  }

  const data = await request(`/api/analysis/${encodeURIComponent(ticker)}`);
  writeCache(cacheKey, data, ANALYSIS_TTL_MS);
  return data;
}

export async function refreshAnalysis(ticker) {
  invalidateAnalysisCache(ticker);
  return fetchAnalysis(ticker, { force: true });
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
