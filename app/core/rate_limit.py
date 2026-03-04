# app/core/rate_limit.py
import time
import threading
from fastapi import HTTPException, status


class InMemoryRateLimiter:
    """
    MVP: in-memory fixed-window limiter.
    Limitation: hanya efektif untuk 1 process.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._buckets: dict[str, tuple[int, float]] = {}  # key -> (count, window_start)

    def hit(self, *, key: str, limit: int, window_seconds: int) -> None:
        now = time.time()
        with self._lock:
            count, start = self._buckets.get(key, (0, now))
            if now - start >= window_seconds:
                count, start = 0, now

            count += 1
            self._buckets[key] = (count, start)

            if count > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests",
                )


limiter = InMemoryRateLimiter()


def rate_limit(*, key: str, limit: int, window_seconds: int = 60):
    """
    Dipakai sebagai Depends().
    """
    def _dep():
        limiter.hit(key=key, limit=limit, window_seconds=window_seconds)
        return True

    return _dep