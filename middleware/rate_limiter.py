import time
import redis
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from config.settings import settings

class APIRateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Try to connect to Redis
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            self.use_redis = True
            print("[INFO] Redis connected for rate limiting.")
        except Exception as e:
            self.use_redis = False
            self.local_limits = {}  # In-memory fallback
            print(f"[WARNING] Redis connection failed: {e}. Falling back to in-memory rate limiting.")

    def _get_tier_limits(self, tier: str) -> tuple:
        """Returns (hourly_limit, concurrent_limit) based on key tier."""
        if tier == "enterprise":
            return 1000, 20
        elif tier == "professional":
            return 100, 5
        else:  # free
            return 10, 1

    def _add_rate_limit_headers(self, response, hourly_limit: int, request_count: int, current_hour: int):
        """Add standard X-RateLimit-* headers to the response."""
        remaining = max(0, hourly_limit - request_count)
        reset_timestamp = (current_hour + 1) * 3600  # Next hour boundary
        response.headers["X-RateLimit-Limit"] = str(hourly_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_timestamp)
        return response

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit public v1 API routes, excluding health check
        path = request.url.path
        if not path.startswith("/api/v1") or path == "/api/v1/health":
            return await call_next(request)

        # Get API key info from request state (populated by APIKeyAuthMiddleware)
        api_key = getattr(request.state, "api_key", None)
        if not api_key:
            return await call_next(request)

        key_id = str(api_key.id)
        tier = api_key.tier
        hourly_limit, max_concurrent = self._get_tier_limits(tier)

        current_time = int(time.time())
        current_hour = current_time // 3600

        # Concurrency and hourly keys
        hourly_key = f"ratelimit:{key_id}:{current_hour}"
        concurrency_key = f"concurrency:{key_id}"
        request_count = 0

        if self.use_redis:
            try:
                # 1. Hourly check
                pipe = self.redis_client.pipeline()
                pipe.incr(hourly_key)
                pipe.expire(hourly_key, 3600)
                request_count, _ = pipe.execute()

                if request_count > hourly_limit:
                    error_resp = JSONResponse(
                        status_code=429,
                        content={"status": "error", "message": "Hourly API rate limit exceeded. Upgrade your tier to increase quota."}
                    )
                    return self._add_rate_limit_headers(error_resp, hourly_limit, request_count, current_hour)

                # 2. Concurrency check
                active_connections = self.redis_client.incr(concurrency_key)
                if active_connections > max_concurrent:
                    self.redis_client.decr(concurrency_key)
                    error_resp = JSONResponse(
                        status_code=429,
                        content={"status": "error", "message": "Too many concurrent requests running. Please serialize your API calls."}
                    )
                    return self._add_rate_limit_headers(error_resp, hourly_limit, request_count, current_hour)

            except redis.RedisError as e:
                # Fallback to call_next on Redis error to maintain availability
                print(f"[ERROR] Redis error in rate limiter: {e}")
                return await call_next(request)
        else:
            # Local fallback (Fixed window hourly + simple concurrency)
            # Cleanup stale keys from previous hours
            stale_keys = [k for k in self.local_limits if ":" in k and not k.startswith("con:") and not k.endswith(str(current_hour))]
            for k in stale_keys:
                del self.local_limits[k]

            # 1. Hourly check
            local_hourly_key = f"{key_id}:{current_hour}"
            self.local_limits.setdefault(local_hourly_key, 0)
            self.local_limits[local_hourly_key] += 1
            request_count = self.local_limits[local_hourly_key]
            if request_count > hourly_limit:
                error_resp = JSONResponse(
                    status_code=429,
                    content={"status": "error", "message": "Hourly API rate limit exceeded."}
                )
                return self._add_rate_limit_headers(error_resp, hourly_limit, request_count, current_hour)

            # 2. Concurrency check
            local_concurrency_key = f"con:{key_id}"
            self.local_limits.setdefault(local_concurrency_key, 0)
            self.local_limits[local_concurrency_key] += 1
            if self.local_limits[local_concurrency_key] > max_concurrent:
                self.local_limits[local_concurrency_key] -= 1
                error_resp = JSONResponse(
                    status_code=429,
                    content={"status": "error", "message": "Too many concurrent requests running."}
                )
                return self._add_rate_limit_headers(error_resp, hourly_limit, request_count, current_hour)

        # Proceed with request execution
        try:
            response = await call_next(request)
            # Attach rate limit headers to successful responses
            self._add_rate_limit_headers(response, hourly_limit, request_count, current_hour)
        finally:
            # Decrement concurrency counter when request completes
            if self.use_redis:
                try:
                    self.redis_client.decr(concurrency_key)
                except redis.RedisError:
                    pass
            else:
                self.local_limits[local_concurrency_key] = max(0, self.local_limits[local_concurrency_key] - 1)

        return response
