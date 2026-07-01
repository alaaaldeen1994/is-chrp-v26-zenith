class ZenithException(Exception):
    """Base exception class for all Zenith API errors."""
    pass

class AuthenticationError(ZenithException):
    """Raised when authentication fails due to invalid or missing API key."""
    pass

class RateLimitError(ZenithException):
    """Raised when hourly or concurrency rate limits are exceeded."""
    pass

class ValidationError(ZenithException):
    """Raised when request payload or params fail backend validation checks."""
    pass

class APIError(ZenithException):
    """Raised when the remote server returns a generic error code."""
    def __init__(self, status_code: int, message: str):
        super().__init__(f"API Error [{status_code}]: {message}")
        self.status_code = status_code
        self.message = message
