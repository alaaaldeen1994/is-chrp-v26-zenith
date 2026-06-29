import time
import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from config.settings import settings

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Injects a transaction-specific correlation trace ID
        request_id = request.headers.get("X-Request-ID", str(int(start_time * 1000)))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000
        
        # Get key information if present
        api_key = getattr(request.state, "api_key", None)
        api_key_id = api_key.id if api_key else None
        owner = api_key.owner if api_key else "anonymous"

        logger.info(
            "request_processed",
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=round(process_time, 2),
            api_key_id=api_key_id,
            owner=owner,
            ip_address=request.client.host if request.client else None
        )
        
        return response
