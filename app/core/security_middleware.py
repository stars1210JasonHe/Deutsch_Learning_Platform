"""
Security middleware for adding security headers and protection
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware:
    """Middleware to add security headers to all responses."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                # Add security headers
                security_headers = {
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY", 
                    b"x-xss-protection": b"1; mode=block",
                    b"strict-transport-security": b"max-age=31536000; includeSubDomains",
                    b"content-security-policy": b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self'",
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                    b"permissions-policy": b"geolocation=(), microphone=(), camera=()"
                }
                
                # Add security headers to response
                for key, value in security_headers.items():
                    if key not in headers:
                        headers[key] = value
                
                message["headers"] = list(headers.items())
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


class RateLimitMiddleware:
    """Simple rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address with proxy header support."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited."""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip] 
                if req_time > minute_ago
            ]
        else:
            self.requests[client_ip] = []
        
        # Check if over limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return True
        
        # Add current request
        self.requests[client_ip].append(now)
        return False
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        client_ip = self._get_client_ip(request)
        
        # Check auth endpoints more strictly 
        path = scope.get("path", "")
        if path.startswith("/auth/"):
            # Stricter rate limiting for auth endpoints
            if self._is_rate_limited(client_ip):
                response = JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests. Please try again later.",
                        "error_code": "RATE_LIMITED"
                    }
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)