"""A tiny in-memory, per-IP rate limiter.

Uses a sliding 60-second window. This keeps the project dependency-free and
easy to follow. It is per-process (state lives in memory), which is fine for a
single-process demo; a production deployment would use Redis or a shared cache.
"""

from collections import defaultdict
from datetime import datetime, timedelta

from django.conf import settings


class RateLimiter:
    def __init__(self):
        self._hits = defaultdict(list)  # ip -> list[datetime]
        self.max_requests = getattr(settings, "RATE_LIMIT_PER_MINUTE", 5)
        self.window = timedelta(seconds=60)

    def is_allowed(self, identifier):
        """Record a request for ``identifier`` and return whether it's allowed."""
        now = datetime.now()
        cutoff = now - self.window
        # Drop timestamps outside the current window.
        recent = [t for t in self._hits[identifier] if t > cutoff]
        if len(recent) >= self.max_requests:
            self._hits[identifier] = recent
            return False
        recent.append(now)
        self._hits[identifier] = recent
        return True


# Module-level singleton shared across requests.
rate_limiter = RateLimiter()
