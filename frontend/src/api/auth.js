const TOKEN_KEY = 'brvm_auth_token';

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

async function authRequest(path, options = {}) {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Erreur API (${response.status})`);
  }
  return data;
}

export function registerAccount(payload) {
  return authRequest('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function loginAccount(payload) {
  return authRequest('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function logoutAccount() {
  return authRequest('/api/auth/logout', { method: 'POST' });
}

export function fetchMe() {
  return authRequest('/api/auth/me');
}

export async function fetchPublicConfig() {
  const response = await fetch('/api/auth/config');
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Erreur API (${response.status})`);
  }
  return data;
}

export function updateProfile(payload) {
  return authRequest('/api/auth/me', {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export function fetchSubscriptionPlans() {
  return authRequest('/api/subscriptions/plans');
}

export function subscribeMonthly(payload = {}) {
  return authRequest('/api/subscriptions/subscribe', {
    method: 'POST',
    body: JSON.stringify({ plan_code: 'pro_monthly', mock_payment: true, ...payload }),
  });
}

export function fetchReferrals() {
  return authRequest('/api/referrals/me');
}
