"""Thread-safe sliding window rate limiter for Cloud Run / FastAPI.

Extracts client IP from the right of the X-Forwarded-For header based on
trusted proxy hops to prevent spoofing. Enforces per-IP and global caps,
guards internal state with a threading.Lock, uses monotonic time and deques,
and bounds memory to 10,000 keys.
"""

from collections import deque
import threading
import time
from typing import Dict, Optional
from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    def __init__(
        self,
        requests_per_minute: int = 10,
        global_per_minute: int = 120,
        trusted_proxy_hops: int = 1,
        max_keys: int = 10_000,
        window_seconds: float = 60.0
    ):
        self.requests_per_minute = requests_per_minute
        self.global_per_minute = global_per_minute
        self.trusted_proxy_hops = trusted_proxy_hops
        self.max_keys = max_keys
        self.window_seconds = window_seconds

        self._lock = threading.Lock()
        # Per-IP timestamps: IP -> deque([monotonic_ts, ...])
        self._ip_records: Dict[str, deque] = {}
        # Global timestamps: deque([monotonic_ts, ...])
        self._global_records: deque = deque()
        self._last_prune: float = time.monotonic()

    def get_client_ip(self, request: Request) -> str:
        """Extract verified client IP from the right of X-Forwarded-For.

        Untrusted client proxies prepend entries to the left. The reverse proxy
        (Cloud Run) appends the verified peer IP to the right. Therefore,
        the true client IP is located at index -trusted_proxy_hops.
        """
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            parts = [p.strip() for p in x_forwarded_for.split(",") if p.strip()]
            if len(parts) >= self.trusted_proxy_hops:
                return parts[-self.trusted_proxy_hops]
            if parts:
                return parts[0]

        if request.client and request.client.host:
            return request.client.host

        return "unknown"

    def _prune_locked(self, now: float) -> None:
        """Prune timestamps older than window_seconds. Must be called while holding _lock."""
        cutoff = now - self.window_seconds

        # Prune global
        while self._global_records and self._global_records[0] <= cutoff:
            self._global_records.popleft()

        # Prune per-IP
        stale_ips = []
        for ip, timestamps in self._ip_records.items():
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if not timestamps:
                stale_ips.append(ip)

        for ip in stale_ips:
            del self._ip_records[ip]

        self._last_prune = now

    def check_rate_limit(self, request: Request) -> None:
        """Enforce rate limits. Raises 429 Too Many Requests if limits are exceeded."""
        client_ip = self.get_client_ip(request)
        now = time.monotonic()

        with self._lock:
            # Periodic pruning every 10 seconds or when table gets large
            if now - self._last_prune > 10.0 or len(self._ip_records) >= self.max_keys:
                self._prune_locked(now)

            # 1. Enforce memory cap (max-keys)
            if client_ip not in self._ip_records and len(self._ip_records) >= self.max_keys:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Server is handling high traffic. Please try again shortly.",
                    headers={"Retry-After": "10"}
                )

            # 2. Enforce global rate limit
            cutoff = now - self.window_seconds
            while self._global_records and self._global_records[0] <= cutoff:
                self._global_records.popleft()

            if len(self._global_records) >= self.global_per_minute:
                oldest_global = self._global_records[0]
                retry_after = max(1, int(self.window_seconds - (now - oldest_global)) + 1)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Global service rate limit reached. Please wait before generating another plan.",
                    headers={"Retry-After": str(retry_after)}
                )

            # 3. Enforce per-IP rate limit
            if client_ip not in self._ip_records:
                self._ip_records[client_ip] = deque()

            ip_deq = self._ip_records[client_ip]
            while ip_deq and ip_deq[0] <= cutoff:
                ip_deq.popleft()

            if len(ip_deq) >= self.requests_per_minute:
                oldest_ip = ip_deq[0]
                retry_after = max(1, int(self.window_seconds - (now - oldest_ip)) + 1)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded for your IP. Please wait before generating another plan.",
                    headers={"Retry-After": str(retry_after)}
                )

            # Record event
            self._global_records.append(now)
            ip_deq.append(now)
