import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Request

from app.core.config import settings
from app.core.exceptions import TooManyRequestsError


class RateLimiter:
    """
    Ковзне вікно (Sliding Window) у пам'яті:
    відстежує часові мітки запитів для кожного IP-клієнта.
    """

    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] >= self.window:
            hits.popleft()
        if len(hits) >= self.limit:
            retry_after = max(1, int(self.window - (now - hits[0])))
            raise TooManyRequestsError(retry_after=retry_after)
        hits.append(now)
        if len(self._hits) > 10_000:
            self._purge(now)

    def _purge(self, now: float) -> None:
        for key in [
            k for k, h in self._hits.items()
            if not h or now - h[-1] >= self.window
        ]:
            del self._hits[key]


# Ініціалізація лімітерів для критичних зон безпеки
_limiters: dict[str, RateLimiter] = {
    "login": RateLimiter(settings.login_rate_limit, settings.rate_limit_window_seconds),
    "register": RateLimiter(settings.register_rate_limit, settings.rate_limit_window_seconds),
    "refresh": RateLimiter(settings.refresh_rate_limit, settings.rate_limit_window_seconds),
}


def rate_limit(scope: str) -> Callable[[Request], None]:
    """Залежність FastAPI для обмеження частоти запитів за IP."""

    def dependency(request: Request) -> None:
        if not settings.rate_limit_enabled:
            return
        limiter = _limiters.get(scope)
        if limiter is None:
            return
        host = request.client.host if request.client else "unknown"
        limiter.check(f"{scope}:{host}")

    return dependency
