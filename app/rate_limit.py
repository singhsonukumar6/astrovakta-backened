"""Small in-process sliding-window rate limiter.

Good enough for single-process deployments; behind multiple workers or a
proxy (where all clients share one IP) move the counter to Redis. Used for
login brute-force protection and the public tenant tool endpoints.
"""
import time
from typing import Dict, List

from fastapi import HTTPException, Request

_buckets: Dict[str, List[float]] = {}
_MAX_KEYS = 50_000


def rate_limit(key: str, max_calls: int, window: float) -> None:
    """Raise 429 when `key` exceeds `max_calls` within `window` seconds."""
    now = time.time()
    hits = [t for t in _buckets.get(key, ()) if now - t < window]
    if len(hits) >= max_calls:
        raise HTTPException(status_code=429, detail="Too many attempts — please try again shortly.")
    hits.append(now)
    _buckets[key] = hits
    if len(_buckets) > _MAX_KEYS:
        # keep memory bounded; dropping history only widens the window briefly
        _buckets.clear()


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"
