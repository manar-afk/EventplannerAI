"""In-memory sliding window rate limiter for Cloud Run / FastAPI.

Extracts client IP from X-Forwarded-For header (first hop from proxy)
or falls back to request.client.host.
Per-instance in-memory storage suitable for single-instance Cloud Run containers.
"""

import time
from typing import Dict, List
from fastapi import Request, HTTPException, status


class InMemoryRateLimiter:
    def __init__(self, requests_per_minute: int = 20):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        # Map: IP -> list of timestamps
        self._requests: Dict[str, List[float]] = {}

    def get_client_ip(self, request: Request) -> str:
        """Extract reliable client IP behind Cloud Run proxy."""
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            # First IP in the list is the original client IP
            client_ip = x_forwarded_for.split(",")[0].strip()
            if client_ip:
                return client_ip

        if request.client and request.client.host:
            return request.client.host

        return "unknown"

    def check_rate_limit(self, request: Request) -> None:
        """Enforce rate limit. Raises 429 Too Many Requests if exceeded."""
        client_ip = self.get_client_ip(request)
        now = time.time()

        if client_ip not in self._requests:
            self._requests[client_ip] = []

        # Retain only timestamps within the rolling window
        cutoff = now - self.window_seconds
        valid_timestamps = [ts for ts in self._requests[client_ip] if ts > cutoff]
        self._requests[client_ip] = valid_timestamps

        if len(valid_timestamps) >= self.requests_per_minute:
            retry_after = int(self.window_seconds - (now - valid_timestamps[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait a moment before generating another plan.",
                headers={"Retry-After": str(max(1, retry_after))}
            )

        self._requests[client_ip].append(now)

    def cleanup_old_records(self) -> None:
        """Periodically prune stale IPs to prevent memory leaks."""
        now = time.time()
        cutoff = now - self.window_seconds
        stale_keys = [
            ip for ip, timestamps in self._requests.items()
            if not timestamps or timestamps[-1] <= cutoff
        ]
        for key in stale_keys:
            del self._requests[key]
