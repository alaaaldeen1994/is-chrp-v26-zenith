import hashlib
from fastapi import Request, HTTPException
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import APIKey
from config.settings import settings

api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)

def verify_api_key(key: str, db: Session) -> APIKey:
    """Hash the key and verify it against database records."""
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    db_key = db.query(APIKey).filter(APIKey.key_hash == key_hash, APIKey.is_active == True).first()
    return db_key

class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Exclude specific paths from API key check (e.g. static pages, swagger, openapi)
        path = request.url.path
        if (
            path in ["/", "/index.html", "/profile", "/discovery", "/health", "/api/docs", "/api/openapi.json", "/api/redoc"] 
            or path.startswith("/static")
            or path.startswith("/css")
            or path.startswith("/js")
            or path.startswith("/assets")
            or not path.startswith("/api/v1")  # Only apply to new public API endpoints
            or path == "/api/v1/health"        # Keep v1 health route open or rate-limited
        ):
            return await call_next(request)

        # Retrieve key from header
        api_key = request.headers.get(settings.API_KEY_HEADER)
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"status": "error", "message": f"Missing authentication header: {settings.API_KEY_HEADER}"}
            )

        db = SessionLocal()
        try:
            db_key = verify_api_key(api_key, db)
            if not db_key:
                return JSONResponse(
                    status_code=401,
                    content={"status": "error", "message": "Invalid or inactive API key"}
                )
            
            # Save key information in request state for downstream routers
            request.state.api_key = db_key
        finally:
            db.close()

        response = await call_next(request)
        return response
