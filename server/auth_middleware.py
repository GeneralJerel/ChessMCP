"""
Authentication Middleware for Chess MCP Server
Verifies OAuth 2.0 access tokens from Google
"""

import jwt
import requests
from typing import Optional, Dict, Any
from functools import lru_cache
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from oauth_config import oauth_config

# Context variable to store current user across async boundaries
current_user_ctx: ContextVar[Optional['UserContext']] = ContextVar('current_user_ctx', default=None)


class UserContext:
    """User context attached to requests after authentication"""
    
    def __init__(self, email: str, user_id: str, name: str = None):
        self.email = email
        self.user_id = user_id
        self.name = name
    
    def __str__(self):
        return f"User({self.email})"


def verify_our_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token signed by our authorization server.
    
    Args:
        token: The JWT token to verify
    
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        # Import here to avoid circular dependency
        from jwt_keys import jwt_key_manager
        
        # Verify the token using our JWT key manager
        payload = jwt_key_manager.verify_jwt(
            token=token,
            issuer=oauth_config.MCP_SERVER_URL,
            audience=oauth_config.MCP_SERVER_URL,
            leeway=oauth_config.TOKEN_LEEWAY
        )
        
        if payload:
            print(f"[Auth] Token verified for user: {payload.get('email')}")
        
        return payload
    
    except Exception as e:
        print(f"[Auth] Token verification error: {e}")
        return None


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify OAuth tokens on protected endpoints.
    
    Skips authentication for:
    - OAuth metadata endpoints (.well-known/*)
    - Health check endpoints
    """
    
    UNAUTHENTICATED_PATHS = [
        "/.well-known/oauth-protected-resource",
        "/.well-known/oauth-authorization-server",
        "/.well-known/oauth-authorization-server/register",
        "/oauth/authorize",  # OAuth authorization endpoint
        "/oauth/callback",   # OAuth callback from Google
        "/oauth/token",      # Token exchange endpoint
        "/oauth/jwks.json",  # Public keys endpoint
        "/health",
        "/docs",
        "/openapi.json",
        "/mcp",  # MCP protocol endpoint - must be accessible for discovery
        "/sse",  # Server-sent events endpoint
    ]
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and verify authentication"""
        
        # Skip authentication for public endpoints
        if any(request.url.path.startswith(path) for path in self.UNAUTHENTICATED_PATHS):
            return await call_next(request)
        
        # Extract Bearer token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header.startswith("Bearer "):
            # No token provided - return 401
            return self._unauthorized_response(request)
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        # Verify the token (our JWT, not Google's)
        payload = verify_our_token(token)
        
        if not payload:
            # Invalid token - return 401
            return self._unauthorized_response(request, error="invalid_token")
        
        # Extract user information from token
        email = payload.get("email")
        user_id = payload.get("sub")
        name = payload.get("name")
        
        if not email or not user_id:
            return self._unauthorized_response(request, error="invalid_token")
        
        # Attach user context to request state AND context variable
        user_context = UserContext(email=email, user_id=user_id, name=name)
        request.state.user = user_context
        
        # Set context variable for access in tools
        current_user_ctx.set(user_context)
        
        # Continue processing the request
        return await call_next(request)
    
    def _unauthorized_response(self, request: Request, error: str = None) -> Response:
        """Generate a 401 Unauthorized response with WWW-Authenticate header"""
        
        www_authenticate = oauth_config.get_www_authenticate_header(
            scope=" ".join(oauth_config.SCOPES)
        )
        
        headers = {"WWW-Authenticate": www_authenticate}
        
        content = {
            "error": error or "authentication_required",
            "error_description": "Valid OAuth 2.0 access token required"
        }
        
        return JSONResponse(
            status_code=401,
            content=content,
            headers=headers
        )


def get_current_user() -> Optional[UserContext]:
    """
    Helper function to get the current authenticated user from context.
    
    Returns:
        UserContext if authenticated, None otherwise
    """
    return current_user_ctx.get()

