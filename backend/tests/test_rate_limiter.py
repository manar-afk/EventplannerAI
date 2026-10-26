"""Tests for thread-safe rate limiter with spoofing protection."""

import concurrent.futures
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException
from backend.app.rate_limiter import InMemoryRateLimiter


def make_request(x_forwarded_for: str = None, client_host: str = "127.0.0.1"):
    req = MagicMock()
    req.headers = {}
    if x_forwarded_for:
        req.headers["x-forwarded-for"] = x_forwarded_for
    req.client.host = client_host
    return req


def test_spoofed_first_x_forwarded_for_entry_does_not_bypass():
    """Requirement: spoofed first X-Forwarded-For entry doesn't bypass the limit."""
    limiter = InMemoryRateLimiter(requests_per_minute=2, trusted_proxy_hops=1)

    # Client tries to spoof IP by prepending different fake IPs:
    # "1.1.1.1, 203.0.113.50", "2.2.2.2, 203.0.113.50", "3.3.3.3, 203.0.113.50"
    # Real client IP from reverse proxy is always 203.0.113.50 (the rightmost hop).
    req1 = make_request("1.1.1.1, 203.0.113.50")
    req2 = make_request("2.2.2.2, 203.0.113.50")
    req3 = make_request("3.3.3.3, 203.0.113.50")

    limiter.check_rate_limit(req1)
    limiter.check_rate_limit(req2)

    # 3rd request from same actual IP must be rejected with 429
    with pytest.raises(HTTPException) as exc_info:
        limiter.check_rate_limit(req3)

    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers


def test_eleventh_request_gets_429():
    """Requirement: 11th request gets 429 with Retry-After (rate_limit_per_minute=10)."""
    limiter = InMemoryRateLimiter(requests_per_minute=10, trusted_proxy_hops=1)
    req = make_request("198.51.100.22")

    for _ in range(10):
        limiter.check_rate_limit(req)

    with pytest.raises(HTTPException) as exc_info:
        limiter.check_rate_limit(req)

    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers


def test_recovers_after_window_with_patched_clock():
    """Requirement: recovers after the window (patched clock)."""
    limiter = InMemoryRateLimiter(requests_per_minute=2, window_seconds=60.0)
    req = make_request("198.51.100.33")

    with patch("time.monotonic", side_effect=[100.0, 101.0, 102.0]):
        limiter.check_rate_limit(req)
        limiter.check_rate_limit(req)
        with pytest.raises(HTTPException):
            limiter.check_rate_limit(req)

    # Fast forward 61 seconds
    with patch("time.monotonic", side_effect=[162.0, 163.0]):
        # Should now succeed without raising 429
        limiter.check_rate_limit(req)


def test_max_keys_cap():
    """Requirement: max-keys cap works and rejects new keys instead of growing unbounded."""
    limiter = InMemoryRateLimiter(requests_per_minute=10, max_keys=3)

    limiter.check_rate_limit(make_request("10.0.0.1"))
    limiter.check_rate_limit(make_request("10.0.0.2"))
    limiter.check_rate_limit(make_request("10.0.0.3"))

    # 4th unique IP should be rejected due to table capacity
    with pytest.raises(HTTPException) as exc_info:
        limiter.check_rate_limit(make_request("10.0.0.4"))

    assert exc_info.value.status_code == 429


def test_concurrency_fifty_threads_never_exceeds_limit():
    """Requirement: 50-thread concurrency never exceeds the limit."""
    limiter = InMemoryRateLimiter(requests_per_minute=15, global_per_minute=50)
    req = make_request("192.168.1.100")

    successes = 0
    rejections = 0

    def call_limit():
        try:
            limiter.check_rate_limit(req)
            return True
        except HTTPException:
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(call_limit) for _ in range(50)]
        for f in concurrent.futures.as_completed(futures):
            if f.result():
                successes += 1
            else:
                rejections += 1

    # Per-IP limit is 15. Exactly 15 requests must succeed, and 35 rejected
    assert successes == 15
    assert rejections == 35
