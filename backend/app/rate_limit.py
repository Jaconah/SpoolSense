"""
Rate limiting configuration for the application.

Provides a shared limiter instance to avoid circular imports.
"""
from fastapi import Request
from slowapi import Limiter


def get_real_ip(request: Request) -> str:
    """
    Get real client IP, reading proxy headers when behind Nginx/Caddy/etc.
    """
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return "unknown"


# Create a single limiter instance to be shared across the application
limiter = Limiter(key_func=get_real_ip)
