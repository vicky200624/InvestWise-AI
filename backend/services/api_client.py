"""
Base API Client for InvestWise AI 3.0 external services.
Enforces Authentication, Retry Logic, Timeout, Redis/In-Memory Caching,
Rate Limiting, Error Handling, Logging, and Monitoring.
"""
import os
import time
import json
import logging
from typing import Any, Dict, Optional, Callable
import urllib.request
import urllib.error
import urllib.parse

logger = logging.getLogger("investwise.services.api_client")

class APIError(Exception):
    """Exception raised for external API communication errors."""
    pass


class BaseAPIClient:
    """
    Base API Client providing:
    - Environment-based Authentication (Never expose API keys)
    - Retry Logic with Exponential Backoff
    - Configurable Request Timeout
    - Redis Caching with TTL (with In-Memory Fallback)
    - Rate Limiting protection
    - Structured Logging & Latency Monitoring
    """
    def __init__(
        self,
        service_name: str,
        api_key_env_var: str,
        base_url: str,
        default_ttl: int = 300,
        max_retries: int = 3,
        timeout: int = 10,
        rate_limit_per_minute: int = 60
    ):
        self.service_name = service_name
        self.api_key_env_var = api_key_env_var
        self.base_url = base_url.rstrip("/")
        self.default_ttl = default_ttl
        self.max_retries = max_retries
        self.timeout = timeout
        self.rate_limit_per_minute = rate_limit_per_minute
        
        # In-memory fallback cache: {cache_key: (timestamp, ttl, data)}
        self._memory_cache: Dict[str, tuple] = {}
        
        # Rate limit tracking
        self._call_timestamps: list = []
        
        # Monitoring stats
        self.stats = {
            "requests_total": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "total_latency_ms": 0.0
        }

    def get_api_key(self) -> str:
        """Read API key securely from environment variables only."""
        key = os.getenv(self.api_key_env_var, "")
        if not key:
            logger.warning(f"[{self.service_name}] API key env var {self.api_key_env_var} is not set.")
        return key

    def _get_redis_client(self):
        """Try to get Redis connection if available."""
        try:
            import redis
            from django.conf import settings
            redis_url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
            client = redis.Redis.from_url(redis_url, socket_connect_timeout=1, decode_responses=True)
            client.ping()
            return client
        except Exception:
            return None

    def cache_get(self, cache_key: str) -> Optional[Any]:
        """Get cached item from Redis or in-memory fallback."""
        redis_client = self._get_redis_client()
        if redis_client:
            try:
                val = redis_client.get(f"investwise:cache:{self.service_name}:{cache_key}")
                if val:
                    self.stats["cache_hits"] += 1
                    return json.loads(val)
            except Exception as e:
                logger.debug(f"[{self.service_name}] Redis cache get failed: {e}")

        # In-memory cache fallback
        if cache_key in self._memory_cache:
            ts, ttl, data = self._memory_cache[cache_key]
            if time.time() - ts <= ttl:
                self.stats["cache_hits"] += 1
                return data
            else:
                del self._memory_cache[cache_key]
                
        self.stats["cache_misses"] += 1
        return None

    def cache_set(self, cache_key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Store item in Redis or in-memory cache with TTL."""
        ttl = ttl if ttl is not None else self.default_ttl
        redis_client = self._get_redis_client()
        if redis_client:
            try:
                redis_client.setex(
                    f"investwise:cache:{self.service_name}:{cache_key}",
                    ttl,
                    json.dumps(data)
                )
                return
            except Exception as e:
                logger.debug(f"[{self.service_name}] Redis cache set failed: {e}")

        # In-memory cache fallback
        self._memory_cache[cache_key] = (time.time(), ttl, data)

    def _check_rate_limit(self) -> None:
        """Enforce client-side rate limiting per minute."""
        now = time.time()
        # Keep only timestamps within last 60 seconds
        self._call_timestamps = [ts for ts in self._call_timestamps if now - ts < 60.0]
        if len(self._call_timestamps) >= self.rate_limit_per_minute:
            sleep_time = 60.0 - (now - self._call_timestamps[0])
            if sleep_time > 0:
                logger.warning(f"[{self.service_name}] Rate limit reached. Sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        self._call_timestamps.append(time.time())

    def execute_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        cache_key: Optional[str] = None,
        ttl: Optional[int] = None,
        fallback_fn: Optional[Callable[[], Any]] = None
    ) -> Any:
        """
        Execute an HTTP GET request with caching, rate limiting, retry logic,
        and fallback handling.
        """
        if cache_key:
            cached_data = self.cache_get(cache_key)
            if cached_data is not None:
                logger.debug(f"[{self.service_name}] Cache HIT for key={cache_key}")
                return cached_data

        self._check_rate_limit()
        self.stats["requests_total"] += 1

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        query_params = params or {}
        api_key = self.get_api_key()
        if api_key and "token" not in query_params and "apikey" not in query_params:
            query_params["apikey"] = api_key

        if query_params:
            url_parts = list(urllib.parse.urlparse(url))
            existing_query = dict(urllib.parse.parse_qsl(url_parts[4]))
            existing_query.update(query_params)
            url_parts[4] = urllib.parse.urlencode(existing_query)
            url = urllib.parse.urlunparse(url_parts)

        start_time = time.time()
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "InvestWiseAI/3.0"}
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    raw_data = response.read().decode("utf-8")
                    data = json.loads(raw_data)

                latency_ms = (time.time() - start_time) * 1000
                self.stats["total_latency_ms"] += latency_ms
                logger.info(
                    f"[{self.service_name}] Request SUCCESS: {endpoint} "
                    f"(attempt={attempt}, latency={latency_ms:.1f}ms)"
                )

                if cache_key:
                    self.cache_set(cache_key, data, ttl=ttl)
                return data

            except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as e:
                last_error = e
                logger.warning(
                    f"[{self.service_name}] Request ERROR on attempt {attempt}/{self.max_retries}: {e}"
                )
                if attempt < self.max_retries:
                    backoff = 2 ** (attempt - 1)
                    time.sleep(backoff)

        self.stats["errors"] += 1
        logger.error(
            f"[{self.service_name}] Request FAILED after {self.max_retries} retries: {last_error}"
        )

        # Trigger fallback if available
        if fallback_fn:
            logger.info(f"[{self.service_name}] Executing fallback_fn for {endpoint}")
            data = fallback_fn()
            if cache_key and data is not None:
                self.cache_set(cache_key, data, ttl=ttl)
            return data

        raise APIError(f"[{self.service_name}] Failed to fetch {endpoint}: {last_error}")

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Return monitoring statistics for API calls and cache hit ratio."""
        total = self.stats["requests_total"] + self.stats["cache_hits"]
        hit_ratio = (self.stats["cache_hits"] / total) if total > 0 else 0.0
        avg_latency = (
            self.stats["total_latency_ms"] / self.stats["requests_total"]
            if self.stats["requests_total"] > 0 else 0.0
        )
        return {
            "service_name": self.service_name,
            "requests_total": self.stats["requests_total"],
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "cache_hit_ratio": round(hit_ratio, 4),
            "errors": self.stats["errors"],
            "avg_latency_ms": round(avg_latency, 2)
        }
