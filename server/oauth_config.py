"""
OAuth 2.1 Configuration for Chess MCP Server
Manages Google OAuth credentials and settings
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class OAuthConfig:
    """OAuth configuration for Google authentication"""
    
    # Google OAuth credentials
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    # MCP Server canonical URI (must be HTTPS in production)
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
    
    # OAuth scopes
    SCOPES: List[str] = ["openid", "email", "profile"]
    
    # Google OAuth endpoints
    GOOGLE_ISSUER = "https://accounts.google.com"
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    GOOGLE_JWKS_URI = "https://www.googleapis.com/oauth2/v3/certs"
    
    # Token validation settings
    TOKEN_ALGORITHM = "RS256"
    TOKEN_LEEWAY = 10  # seconds of leeway for clock skew
    
    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is present"""
        errors = []
        
        if not cls.GOOGLE_CLIENT_ID:
            errors.append("GOOGLE_CLIENT_ID environment variable is required")
        
        if not cls.GOOGLE_CLIENT_SECRET:
            errors.append("GOOGLE_CLIENT_SECRET environment variable is required")
        
        if not cls.MCP_SERVER_URL:
            errors.append("MCP_SERVER_URL environment variable is required")
        
        if errors:
            raise ValueError(
                "OAuth configuration incomplete:\n" + "\n".join(f"  - {e}" for e in errors)
            )
    
    @classmethod
    def get_protected_resource_metadata(cls) -> dict:
        """Get RFC 9728 protected resource metadata"""
        return {
            "resource": cls.MCP_SERVER_URL,
            "authorization_servers": [cls.MCP_SERVER_URL],  # Point to ourselves, not Google
            "scopes_supported": cls.SCOPES,
            "resource_documentation": f"{cls.MCP_SERVER_URL}/docs"
        }
    
    @classmethod
    def get_www_authenticate_header(cls, scope: str = None) -> str:
        """Generate WWW-Authenticate header value for 401 responses"""
        metadata_url = f"{cls.MCP_SERVER_URL}/.well-known/oauth-protected-resource"
        
        parts = [f'Bearer resource_metadata="{metadata_url}"']
        
        if scope:
            parts.append(f'scope="{scope}"')
        
        return ", ".join(parts)


# Singleton instance
oauth_config = OAuthConfig()

