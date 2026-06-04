const DEFAULT_TTL_MS = 10 * 60 * 1000;

const store = new Map();

export function readCache(key) {
  const entry = store.get(key);
  if (!entry) {
    return null;
  }
  if (Date.now() > entry.expiresAt) {
    store.delete(key);
    return null;
  }
  return entry.value;
}

export function writeCache(key, value, ttlMs = DEFAULT_TTL_MS) {
  store.set(key, { value, expiresAt: Date.now() + ttlMs });
}

export function deleteCache(key) {
  store.delete(key);
}
