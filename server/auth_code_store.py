"""
Authorization Code Store for OAuth 2.1
Manages authorization codes and PKCE validation
"""

import uuid
import threading
import time
import hashlib
import base64
from typing import Dict, Optional


class AuthorizationCode:
    """Represents an authorization code with associated data"""
    
    def __init__(
        self,
        code: str,
        google_access_token: str,
        google_id_token: str,
        user_info: dict,
        client_id: str,
        code_challenge: str,
        code_challenge_method: str,
        redirect_uri: str,
        scope: str,
        expires_at: float
    ):
        self.code = code
        self.google_access_token = google_access_token
        self.google_id_token = google_id_token
        self.user_info = user_info
        self.client_id = client_id
        self.code_challenge = code_challenge
        self.code_challenge_method = code_challenge_method
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.expires_at = expires_at
        self.used = False


class AuthCodeStore:
    """
    Thread-safe storage for authorization codes.
    Implements PKCE validation and code expiration.
    """
    
    def __init__(self, code_lifetime: int = 600):
        """
        Initialize the authorization code store.
        
        Args:
            code_lifetime: Lifetime of authorization codes in seconds (default: 10 minutes)
        """
        self._codes: Dict[str, AuthorizationCode] = {}
        self._lock = threading.Lock()
        self._code_lifetime = code_lifetime
    
    def create_code(
        self,
        google_access_token: str,
        google_id_token: str,
        user_info: dict,
        client_id: str,
        code_challenge: str,
        code_challenge_method: str,
        redirect_uri: str,
        scope: str
    ) -> str:
        """
        Create a new authorization code.
        
        Args:
            google_access_token: Access token from Google
            google_id_token: ID token from Google
            user_info: User information from Google
            client_id: The client ID requesting the code
            code_challenge: PKCE code challenge
            code_challenge_method: PKCE method (S256 or plain)
            redirect_uri: The redirect URI
            scope: Requested scopes
        
        Returns:
            The generated authorization code
        """
        with self._lock:
            # Generate unique authorization code
            code = f"code_{uuid.uuid4().hex}"
            
            # Create authorization code object
            auth_code = AuthorizationCode(
                code=code,
                google_access_token=google_access_token,
                google_id_token=google_id_token,
                user_info=user_info,
                client_id=client_id,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
                redirect_uri=redirect_uri,
                scope=scope,
                expires_at=time.time() + self._code_lifetime
            )
            
            # Store it
            self._codes[code] = auth_code
            
            print(f"[AuthCodeStore] Created authorization code for client {client_id}")
            
            return code
    
    def exchange_code(
        self,
        code: str,
        code_verifier: str,
        client_id: str,
        redirect_uri: str
    ) -> Optional[AuthorizationCode]:
        """
        Exchange an authorization code for token data.
        Validates PKCE code_verifier and ensures code hasn't been used.
        
        Args:
            code: The authorization code
            code_verifier: PKCE code verifier
            client_id: The client ID
            redirect_uri: The redirect URI (must match original)
        
        Returns:
            AuthorizationCode if valid, None otherwise
        """
        with self._lock:
            auth_code = self._codes.get(code)
            
            if not auth_code:
                print(f"[AuthCodeStore] Code not found: {code}")
                return None
            
            # Check if already used
            if auth_code.used:
                print(f"[AuthCodeStore] Code already used: {code}")
                # Security: invalidate all tokens for this client
                del self._codes[code]
                return None
            
            # Check expiration
            if time.time() > auth_code.expires_at:
                print(f"[AuthCodeStore] Code expired: {code}")
                del self._codes[code]
                return None
            
            # Validate client ID
            if auth_code.client_id != client_id:
                print(f"[AuthCodeStore] Client ID mismatch for code: {code}")
                return None
            
            # Validate redirect URI
            if auth_code.redirect_uri != redirect_uri:
                print(f"[AuthCodeStore] Redirect URI mismatch for code: {code}")
                return None
            
            # Validate PKCE code_verifier
            if not self._validate_pkce(code_verifier, auth_code.code_challenge, auth_code.code_challenge_method):
                print(f"[AuthCodeStore] PKCE validation failed for code: {code}")
                return None
            
            # Mark as used and return
            auth_code.used = True
            
            print(f"[AuthCodeStore] Code exchanged successfully for client {client_id}")
            
            return auth_code
    
    def _validate_pkce(self, code_verifier: str, code_challenge: str, method: str) -> bool:
        """
        Validate PKCE code_verifier against code_challenge.
        
        Args:
            code_verifier: The code verifier from token request
            code_challenge: The code challenge from authorization request
            method: The challenge method (S256 or plain)
        
        Returns:
            True if valid, False otherwise
        """
        if method == "S256":
            # Hash the verifier with SHA256 and base64url encode
            verifier_hash = hashlib.sha256(code_verifier.encode('ascii')).digest()
            computed_challenge = base64.urlsafe_b64encode(verifier_hash).decode('ascii').rstrip('=')
            return computed_challenge == code_challenge
        elif method == "plain":
            # Plain method: verifier must equal challenge
            return code_verifier == code_challenge
        else:
            print(f"[AuthCodeStore] Unknown PKCE method: {method}")
            return False
    
    def cleanup_expired(self) -> int:
        """
        Remove expired authorization codes.
        
        Returns:
            Number of codes removed
        """
        with self._lock:
            now = time.time()
            expired = [
                code for code, auth_code in self._codes.items()
                if now > auth_code.expires_at or auth_code.used
            ]
            
            for code in expired:
                del self._codes[code]
            
            if expired:
                print(f"[AuthCodeStore] Cleaned up {len(expired)} expired/used codes")
            
            return len(expired)
    
    def count(self) -> int:
        """Get total number of active authorization codes"""
        with self._lock:
            return len(self._codes)


# Global authorization code store instance
auth_code_store = AuthCodeStore()

