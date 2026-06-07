import { apiUrl } from '../config/api';
import { getAuthToken } from './auth';

async function userRequest(path, options = {}) {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(apiUrl(path), { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Erreur API (${response.status})`);
  }
  return data;
}

export function fetchWatchlist() {
  return userRequest('/api/user/watchlist');
}

export function fetchWatchlistStatus(ticker) {
  return userRequest(`/api/user/watchlist/${encodeURIComponent(ticker)}/status`);
}

export function addWatchlistItem(ticker) {
  return userRequest('/api/user/watchlist', {
    method: 'POST',
    body: JSON.stringify({ ticker }),
  });
}

export function removeWatchlistItem(ticker) {
  return userRequest(`/api/user/watchlist/${encodeURIComponent(ticker)}`, {
    method: 'DELETE',
  });
}

export function fetchAlerts() {
  return userRequest('/api/user/alerts');
}

export function createAlert(payload) {
  return userRequest('/api/user/alerts', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updateAlert(alertId, payload) {
  return userRequest(`/api/user/alerts/${alertId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export function deleteAlert(alertId) {
  return userRequest(`/api/user/alerts/${alertId}`, { method: 'DELETE' });
}
