"""
Rate limiting simple (Redis ou mémoire) pour l'API publique.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Optional

from flask import Request

_memory_buckets: dict[str, tuple[int, float]] = {}
_memory_lock = threading.Lock()


def _enabled() -> bool:
    return os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("1", "true", "yes")


def _limit_per_minute() -> int:
    return int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))


def _client_key(request: Request) -> str:
    forwarded = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    remote = forwarded or request.remote_addr or "unknown"
    token = request.headers.get("Authorization", "")[:32]
    if token:
        return f"auth:{token}"
    return f"ip:{remote}"


def _check_redis(key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    from storage.cache_service import get_redis_client

    client = get_redis_client()
    if not client:
        return _check_memory(key, limit, window_seconds)

    redis_key = f"brvm:ratelimit:{key}"
    try:
        count = client.incr(redis_key)
        if count == 1:
            client.expire(redis_key, window_seconds)
        remaining = max(0, limit - count)
        return count <= limit, remaining
    except Exception:
        return _check_memory(key, limit, window_seconds)


def _check_memory(key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    now = time.time()
    with _memory_lock:
        bucket = _memory_buckets.get(key)
        if not bucket or bucket[1] <= now:
            _memory_buckets[key] = (1, now + window_seconds)
            return True, limit - 1
        count, expires = bucket
        if count >= limit:
            return False, 0
        _memory_buckets[key] = (count + 1, expires)
        return True, limit - count - 1


def check_request_limit(request: Request) -> Optional[dict]:
    """
    Retourne None si OK, sinon dict d'erreur 429.
    """
    if not _enabled():
        return None

    if request.method == "OPTIONS":
        return None

    path = request.path or ""
    if not path.startswith("/api/"):
        return None
    if path.startswith("/api/health"):
        return None

    limit = _limit_per_minute()
    key = _client_key(request)
    allowed, remaining = _check_redis(key, limit, 60)

    if allowed:
        return None

    return {
        "error": "Trop de requêtes. Réessayez dans une minute.",
        "retry_after_seconds": 60,
        "limit_per_minute": limit,
        "remaining": remaining,
    }
