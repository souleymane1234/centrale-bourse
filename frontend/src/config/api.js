/** Base URL API (sans slash final). Vide = appels relatifs `/api/...` (même origine Nginx). */
export function getApiBase() {
  const raw = import.meta.env.VITE_API_BASE;
  if (raw == null || String(raw).trim() === '') {
    return '';
  }
  return String(raw).replace(/\/$/, '');
}

export function apiUrl(path) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${getApiBase()}${normalizedPath}`;
}
