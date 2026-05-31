"""
Cache partagé (Redis) avec repli mémoire, verrou anti-stampede et service stale.

Utilisé par l'API pour éviter les recalculs / scrapes simultanés sous charge.
"""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Callable, Optional

CACHE_PREFIX = os.getenv("CACHE_KEY_PREFIX", "brvm:v1")
_redis_client = None
_redis_init_attempted = False
_redis_lock = threading.Lock()

# Repli mémoire (dev sans Redis)
_memory_entries: dict[str, tuple[float, Any]] = {}
_memory_stale: dict[str, tuple[float, Any]] = {}
_memory_lock = threading.Lock()


def _redis_url() -> str:
    return (os.getenv("REDIS_URL") or "").strip()


def redis_enabled() -> bool:
    return bool(_redis_url())


def get_redis_client():
    """Client Redis unique (lazy). Retourne None si indisponible."""
    global _redis_client, _redis_init_attempted

    if not _redis_url():
        return None

    with _redis_lock:
        if _redis_init_attempted:
            return _redis_client
        _redis_init_attempted = True
        try:
            import redis

            client = redis.from_url(
                _redis_url(),
                decode_responses=True,
                socket_connect_timeout=float(os.getenv("REDIS_CONNECT_TIMEOUT", "2")),
                socket_timeout=float(os.getenv("REDIS_SOCKET_TIMEOUT", "5")),
            )
            client.ping()
            _redis_client = client
            print("✅ Cache Redis connecté.")
        except Exception as exc:
            print(f"⚠️  Redis indisponible, cache mémoire local : {exc}")
            _redis_client = None
        return _redis_client


def _full_key(key: str) -> str:
    return f"{CACHE_PREFIX}:{key}"


def _stale_key(key: str) -> str:
    return f"{CACHE_PREFIX}:{key}:stale"


def _lock_key(key: str) -> str:
    return f"{CACHE_PREFIX}:lock:{key}"


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _json_loads(raw: str) -> Any:
    return json.loads(raw)


def _memory_get(key: str) -> Optional[Any]:
    now = time.time()
    with _memory_lock:
        entry = _memory_entries.get(key)
        if entry and entry[0] > now:
            return entry[1]
    return None


def _memory_get_stale(key: str) -> Optional[Any]:
    now = time.time()
    with _memory_lock:
        for store in (_memory_entries, _memory_stale):
            entry = store.get(key)
            if entry and entry[0] > now:
                return entry[1]
    return None


def _memory_set(key: str, value: Any, ttl_seconds: int, *, stale: bool = False) -> None:
    expires = time.time() + max(1, ttl_seconds)
    with _memory_lock:
        target = _memory_stale if stale else _memory_entries
        target[key] = (expires, value)


def _memory_delete(key: str) -> None:
    with _memory_lock:
        _memory_entries.pop(key, None)
        _memory_stale.pop(key, None)


def cache_get(key: str) -> Optional[Any]:
    """Lit une entrée cache (Redis ou mémoire)."""
    client = get_redis_client()
    if client:
        try:
            raw = client.get(_full_key(key))
            if raw is not None:
                return _json_loads(raw)
        except Exception as exc:
            print(f"⚠️  cache_get Redis ({key}) : {exc}")
    return _memory_get(key)


def cache_get_stale(key: str) -> Optional[Any]:
    """Lit la version stale si le cache principal est expiré."""
    client = get_redis_client()
    if client:
        try:
            raw = client.get(_stale_key(key))
            if raw is not None:
                return _json_loads(raw)
        except Exception as exc:
            print(f"⚠️  cache_get_stale Redis ({key}) : {exc}")
    return _memory_get_stale(key)


def cache_set(
    key: str,
    value: Any,
    ttl_seconds: int,
    *,
    stale_ttl_seconds: Optional[int] = None,
) -> None:
    """Écrit cache principal + copie stale (TTL plus long)."""
    stale_ttl = stale_ttl_seconds if stale_ttl_seconds is not None else max(ttl_seconds * 10, 3600)
    payload = _json_dumps(value)
    stale_payload = payload

    client = get_redis_client()
    if client:
        try:
            pipe = client.pipeline()
            pipe.setex(_full_key(key), max(1, ttl_seconds), payload)
            pipe.setex(_stale_key(key), max(1, stale_ttl), stale_payload)
            pipe.execute()
            return
        except Exception as exc:
            print(f"⚠️  cache_set Redis ({key}) : {exc}")

    _memory_set(key, value, ttl_seconds, stale=False)
    _memory_set(key, value, stale_ttl, stale=True)


def cache_delete(key: str) -> None:
    client = get_redis_client()
    if client:
        try:
            client.delete(_full_key(key), _stale_key(key), _lock_key(key))
        except Exception as exc:
            print(f"⚠️  cache_delete Redis ({key}) : {exc}")
    _memory_delete(key)


def invalidate_keys(*keys: str) -> None:
    for key in keys:
        cache_delete(key)


def invalidate_pattern(pattern: str) -> None:
    """Supprime les clés dont le suffixe correspond (ex. analysis:)."""
    client = get_redis_client()
    if client:
        try:
            match = f"{CACHE_PREFIX}:{pattern}*"
            keys = list(client.scan_iter(match=match, count=200))
            if keys:
                client.delete(*keys)
        except Exception as exc:
            print(f"⚠️  invalidate_pattern Redis ({pattern}) : {exc}")

    if pattern.endswith(":"):
        prefix = pattern
        with _memory_lock:
            for store in (_memory_entries, _memory_stale):
                for key in list(store.keys()):
                    if key.startswith(prefix):
                        store.pop(key, None)


def acquire_build_lock(key: str, lock_seconds: int = 120) -> bool:
    """True si ce processus doit construire la valeur."""
    client = get_redis_client()
    if client:
        try:
            return bool(client.set(_lock_key(key), "1", nx=True, ex=max(5, lock_seconds)))
        except Exception as exc:
            print(f"⚠️  acquire_build_lock Redis ({key}) : {exc}")
    # Mémoire : verrou simple par clé
    lock_name = f"memlock:{key}"
    with _memory_lock:
        entry = _memory_entries.get(lock_name)
        if entry and entry[0] > time.time():
            return False
        _memory_entries[lock_name] = (time.time() + lock_seconds, True)
        return True


def release_build_lock(key: str) -> None:
    client = get_redis_client()
    if client:
        try:
            client.delete(_lock_key(key))
        except Exception:
            pass
    with _memory_lock:
        _memory_entries.pop(f"memlock:{key}", None)


def get_or_build(
    key: str,
    ttl_seconds: int,
    builder: Callable[[], Any],
    *,
    lock_seconds: int = 120,
    stale_ttl_seconds: Optional[int] = None,
    wait_seconds: float = 15.0,
    poll_interval: float = 0.25,
) -> tuple[Any, str]:
    """
    Retourne (valeur, état_cache).
    état_cache : hit | built | stale | wait_stale
    """
    cached = cache_get(key)
    if cached is not None:
        return cached, "hit"

    if acquire_build_lock(key, lock_seconds=lock_seconds):
        try:
            cached = cache_get(key)
            if cached is not None:
                return cached, "hit"
            value = builder()
            cache_set(key, value, ttl_seconds, stale_ttl_seconds=stale_ttl_seconds)
            return value, "built"
        finally:
            release_build_lock(key)

    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        cached = cache_get(key)
        if cached is not None:
            return cached, "hit"
        time.sleep(poll_interval)

    stale = cache_get_stale(key)
    if stale is not None:
        return stale, "stale"

    # Dernier recours : un seul builder sans attendre indéfiniment
    if acquire_build_lock(key, lock_seconds=lock_seconds):
        try:
            value = builder()
            cache_set(key, value, ttl_seconds, stale_ttl_seconds=stale_ttl_seconds)
            return value, "built"
        finally:
            release_build_lock(key)

    stale = cache_get_stale(key)
    if stale is not None:
        return stale, "wait_stale"
    raise TimeoutError(f"Impossible de construire le cache pour {key}")


def cache_status() -> dict:
    """État du cache pour /api/health."""
    return {
        "redis_configured": redis_enabled(),
        "redis_connected": get_redis_client() is not None,
        "prefix": CACHE_PREFIX,
        "backend": "redis" if get_redis_client() else "memory",
    }
