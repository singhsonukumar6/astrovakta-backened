"""Redis-backed cache for frequently-computed values.

Reduces DB hits for API key validation and Swiss Ephemeris CPU time.
Gracefully degrades when Redis is unavailable.
"""

import os
import json
import hashlib
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0").strip()
_redis = None


def _get_redis():
    global _redis
    if _redis is None and REDIS_URL:
        try:
            import redis as _redis_mod
            _redis = _redis_mod.from_url(REDIS_URL, decode_responses=True)
            _redis.ping()
            logger.info(f"Redis connected: {REDIS_URL}")
        except Exception as e:
            logger.warning(f"Redis unavailable, caching disabled: {e}")
            _redis = False  # Sentinel
    return _redis if _redis else None


def get(key: str) -> Optional[str]:
    r = _get_redis()
    if not r:
        return None
    try:
        return r.get(key)
    except Exception as e:
        logger.debug(f"Redis get failed: {e}")
        return None


def set(key: str, value: str, ttl: int = 300) -> bool:
    r = _get_redis()
    if not r:
        return False
    try:
        r.setex(key, ttl, value)
        return True
    except Exception as e:
        logger.debug(f"Redis set failed: {e}")
        return False


def delete(key: str) -> bool:
    r = _get_redis()
    if not r:
        return False
    try:
        r.delete(key)
        return True
    except Exception as e:
        logger.debug(f"Redis delete failed: {e}")
        return False


def cache_key(prefix: str, *args) -> str:
    raw = ":".join(str(a) for a in args)
    h = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"{prefix}:{h}"


def get_or_compute(key: str, compute_fn, ttl: int = 300) -> Any:
    cached = get(key)
    if cached is not None:
        try:
            return json.loads(cached)
        except (json.JSONDecodeError, TypeError):
            return cached
    result = compute_fn()
    try:
        set(key, json.dumps(result) if not isinstance(result, str) else result, ttl)
    except Exception:
        pass
    return result
