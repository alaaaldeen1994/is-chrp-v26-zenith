"""
Security Middleware for Nilus Lab Platform
Implements XSS, CSRF, and Rate Limiting Protection
"""

from fastapi import Request, HTTPException, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import bleach
import os
import secrets
from typing import Optional
import time

# ==================== CSRF Protection ====================

class CSRFProtection:
    """
    Implements Double-Submit Cookie Pattern for CSRF Protection
    """
    def __init__(self, secret_key: str):
        self.serializer = URLSafeTimedSerializer(secret_key)
        self.token_max_age = 3600  # 1 hour
    
    def generate_token(self) -> str:
        """Generate a new CSRF token"""
        random_data = secrets.token_urlsafe(32)
        return self.serializer.dumps(random_data)
    
    def validate_token(self, token: str) -> bool:
        """Validate CSRF token"""
        try:
            self.serializer.loads(token, max_age=self.token_max_age)
            return True
        except (BadSignature, SignatureExpired):
            return False


# Initialize CSRF with secret key from environment
csrf_protection = CSRFProtection(
    secret_key=os.getenv("SECRET_KEY", "zenith-v26-fallback-key-CHANGE-IN-PRODUCTION")
)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce CSRF protection on state-changing requests
    """
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF for safe methods and health checks
        if request.method in ["GET", "HEAD", "OPTIONS"] or request.url.path == "/health":
            return await call_next(request)
        
        # Skip CSRF for paths that use API Key authentication
        api_key_paths = [
            "/simulate_step", "/discover_protocol", "/discover_hybrid", "/impute", 
            "/get_expert_reasoning", "/send_email", "/api/simulation/config", "/run_virtual_trial"
        ]
        if request.url.path in api_key_paths:
            return await call_next(request)
        
        # Validate CSRF token for all other POST/PUT/DELETE requests
        csrf_token = request.headers.get("X-CSRF-Token") or request.cookies.get("csrf_token")
        
        if not csrf_token or not csrf_protection.validate_token(csrf_token):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF validation failed"}
            )
        
        return await call_next(request)


# ==================== XSS Protection ====================

def sanitize_input(text: str, allowed_tags: Optional[list] = None) -> str:
    """
    Sanitize user input to prevent XSS attacks
    
    Args:
        text: Raw user input
        allowed_tags: List of allowed HTML tags (default: none, strips all HTML)
    
    Returns:
        Sanitized text safe for display
    """
    if allowed_tags is None:
        allowed_tags = []  # Strip all HTML by default
    
    return bleach.clean(
        text,
        tags=allowed_tags,
        strip=True,
        strip_comments=True
    )


def sanitize_dict(data: dict) -> dict:
    """Recursively sanitize all string values in a dictionary"""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_input(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_input(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


# ==================== Rate Limiting ====================

limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    "auth": "5/minute",          # Login/signup attempts
    "discovery": "20/minute",    # AI analysis requests  
    "simulation": "100/minute",  # Simulation steps
    "general": "60/minute"       # General API calls
}


# ==================== Session Security ====================

class SessionManager:
    """
    Secure session management with HTTP-only cookies
    """
    def __init__(self, secret_key: str):
        self.serializer = URLSafeTimedSerializer(secret_key)
        self.session_max_age = 86400  # 24 hours
        self.refresh_token_max_age = 604800  # 7 days
    
    def create_session_token(self, user_id: str) -> str:
        """Create secure session token"""
        payload = {
            "user_id": user_id,
            "created_at": time.time()
        }
        return self.serializer.dumps(payload)
    
    def validate_session_token(self, token: str) -> Optional[dict]:
        """Validate and decode session token"""
        try:
            payload = self.serializer.loads(token, max_age=self.session_max_age)
            return payload
        except (BadSignature, SignatureExpired):
            return None
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token for session renewal"""
        payload = {
            "user_id": user_id,
            "type": "refresh",
            "created_at": time.time()
        }
        return self.serializer.dumps(payload)
    
    def validate_refresh_token(self, token: str) -> Optional[str]:
        """Validate refresh token and return user_id"""
        try:
            payload = self.serializer.loads(token, max_age=self.refresh_token_max_age)
            if payload.get("type") == "refresh":
                return payload.get("user_id")
        except (BadSignature, SignatureExpired):
            pass
        return None


# Initialize session manager
session_manager = SessionManager(
    secret_key=os.getenv("SECRET_KEY", "zenith-v26-fallback-key-CHANGE-IN-PRODUCTION")
)


# ==================== Security Headers Middleware ====================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # BROAD CSP: Restoration Priority
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' * data: blob: 'unsafe-inline' 'unsafe-eval'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' *; "
            "style-src 'self' 'unsafe-inline' *; "
            "img-src 'self' data: blob: *; "
            "font-src 'self' data: *; "
            "connect-src 'self' * wss: ws:; "
            "frame-src 'self' *; "
            "worker-src 'self' blob:; "
            "child-src 'self' blob:; "
            "object-src 'none';"
        )
        
        return response
