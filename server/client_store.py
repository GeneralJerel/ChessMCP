"""
Client Registration Store for OAuth 2.1 Dynamic Client Registration
Manages registered OAuth clients for ChatGPT
"""

import uuid
import threading
import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ClientRegistration:
    """Represents a registered OAuth client"""
    client_id: str
    client_secret: str
    redirect_uris: List[str]
    grant_types: List[str]
    response_types: List[str]
    token_endpoint_auth_method: str
    created_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to RFC 7591 response format"""
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uris": self.redirect_uris,
            "grant_types": self.grant_types,
            "response_types": self.response_types,
            "token_endpoint_auth_method": self.token_endpoint_auth_method,
            "client_id_issued_at": int(self.created_at),
        }


class ClientStore:
    """
    Thread-safe storage for registered OAuth clients.
    In-memory storage for development; use Redis/database for production.
    """
    
    def __init__(self):
        self._clients: Dict[str, ClientRegistration] = {}
        self._lock = threading.Lock()
        self._cleanup_interval = 3600  # Cleanup every hour
        self._max_age = 86400 * 7  # Keep registrations for 7 days
    
    def register_client(
        self, 
        redirect_uris: List[str],
        grant_types: List[str] = None,
        response_types: List[str] = None,
        metadata: dict = None
    ) -> ClientRegistration:
        """
        Register a new OAuth client.
        
        Args:
            redirect_uris: List of allowed redirect URIs
            grant_types: OAuth grant types (defaults to authorization_code, refresh_token)
            response_types: OAuth response types (defaults to code)
            metadata: Additional client metadata
        
        Returns:
            ClientRegistration with generated credentials
        """
        with self._lock:
            # Generate unique client ID
            client_id = f"chess-mcp-{uuid.uuid4().hex[:16]}"
            
            # Generate client secret
            client_secret = f"secret-{uuid.uuid4().hex}"
            
            # Create registration
            registration = ClientRegistration(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uris=redirect_uris or [],
                grant_types=grant_types or ["authorization_code", "refresh_token"],
                response_types=response_types or ["code"],
                token_endpoint_auth_method="client_secret_post",
                metadata=metadata or {}
            )
            
            # Store registration
            self._clients[client_id] = registration
            
            print(f"[ClientStore] Registered new client: {client_id}")
            
            return registration
    
    def get_client(self, client_id: str) -> Optional[ClientRegistration]:
        """
        Retrieve a registered client by ID.
        
        Args:
            client_id: The client identifier
        
        Returns:
            ClientRegistration if found, None otherwise
        """
        with self._lock:
            return self._clients.get(client_id)
    
    def validate_client(self, client_id: str, client_secret: str) -> bool:
        """
        Validate client credentials.
        
        Args:
            client_id: The client identifier
            client_secret: The client secret
        
        Returns:
            True if credentials are valid, False otherwise
        """
        with self._lock:
            client = self._clients.get(client_id)
            if not client:
                return False
            return client.client_secret == client_secret
    
    def validate_redirect_uri(self, client_id: str, redirect_uri: str) -> bool:
        """
        Validate that a redirect URI is registered for the client.
        
        Args:
            client_id: The client identifier
            redirect_uri: The redirect URI to validate
        
        Returns:
            True if URI is registered, False otherwise
        """
        with self._lock:
            client = self._clients.get(client_id)
            if not client:
                return False
            return redirect_uri in client.redirect_uris
    
    def cleanup_expired(self) -> int:
        """
        Remove expired client registrations.
        
        Returns:
            Number of clients removed
        """
        with self._lock:
            now = time.time()
            expired = [
                client_id for client_id, client in self._clients.items()
                if now - client.created_at > self._max_age
            ]
            
            for client_id in expired:
                del self._clients[client_id]
            
            if expired:
                print(f"[ClientStore] Cleaned up {len(expired)} expired clients")
            
            return len(expired)
    
    def count(self) -> int:
        """Get total number of registered clients"""
        with self._lock:
            return len(self._clients)


# Global client store instance
client_store = ClientStore()

