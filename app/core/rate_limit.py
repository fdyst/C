# app/core/rate_limit.py
import time
import threading
from fastapi import HTTPException, status, Request


class InMemoryRateLimiter:
    """
    MVP limiter: efektif untuk 1 proses.
    Kalau nanti scale multi-worker, pindah Redis.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._buckets: dict[str, tuple[int, float]] = {}  # key -> (count, window_start)

    def hit(self, *, key: str, limit: int, window_seconds: int) -> None:
        now = time.time()
        with self._lock:
            count, start = self._buckets.get(key, (0, now))

            # reset window
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


def rate_limit_dep(*, prefix: str, limit: int, window_seconds: int = 60):
    """
    Pakai sebagai Depends().
    Key otomatis: prefix + IP client.
    """
    def _dep(request: Request):
        ip = request.client.host if request.client else "unknown"
        limiter.hit(key=f"{prefix}:{ip}", limit=limit, window_seconds=window_seconds)
        return True

    return _dep
