"""
JWT Key Management for OAuth 2.1
Generates and manages RSA keys for signing access tokens
"""

import jwt
import time
import base64
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


class JWTKeyManager:
    """
    Manages RSA key pair for JWT signing and verification.
    Generates keys on startup and publishes public key via JWKS.
    """
    
    def __init__(self, key_id: str = "chess-mcp-key-1"):
        """
        Initialize the JWT key manager.
        
        Args:
            key_id: Identifier for the key (used in JWT header and JWKS)
        """
        self.key_id = key_id
        self._generate_key_pair()
        print(f"[JWTKeyManager] Generated RSA key pair with kid: {self.key_id}")
    
    def _generate_key_pair(self):
        """Generate RSA 2048-bit key pair"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
    
    def sign_jwt(
        self,
        subject: str,
        email: str,
        name: str,
        issuer: str,
        audience: str,
        scope: str = "openid email profile",
        expires_in: int = 3600
    ) -> str:
        """
        Sign a JWT access token with our private key.
        
        Args:
            subject: User ID (sub claim)
            email: User email
            name: User name
            issuer: Token issuer (our server URL)
            audience: Token audience (our server URL)
            scope: OAuth scopes
            expires_in: Token lifetime in seconds (default: 1 hour)
        
        Returns:
            Signed JWT token string
        """
        now = int(time.time())
        
        payload = {
            # Standard JWT claims
            "iss": issuer,
            "aud": audience,
            "sub": subject,
            "iat": now,
            "exp": now + expires_in,
            "nbf": now,
            
            # User claims
            "email": email,
            "name": name,
            "email_verified": True,
            
            # OAuth claims
            "scope": scope,
        }
        
        # Sign with RS256
        token = jwt.encode(
            payload,
            self.private_key,
            algorithm="RS256",
            headers={"kid": self.key_id}
        )
        
        return token
    
    def verify_jwt(
        self,
        token: str,
        issuer: str,
        audience: str,
        leeway: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Verify a JWT token signed with our private key.
        
        Args:
            token: The JWT token to verify
            issuer: Expected issuer
            audience: Expected audience
            leeway: Clock skew leeway in seconds
        
        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=["RS256"],
                issuer=issuer,
                audience=audience,
                leeway=leeway,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )
            return payload
        except jwt.ExpiredSignatureError:
            print("[JWTKeyManager] Token expired")
            return None
        except jwt.InvalidAudienceError:
            print("[JWTKeyManager] Invalid audience")
            return None
        except jwt.InvalidIssuerError:
            print("[JWTKeyManager] Invalid issuer")
            return None
        except jwt.InvalidTokenError as e:
            print(f"[JWTKeyManager] Invalid token: {e}")
            return None
        except Exception as e:
            print(f"[JWTKeyManager] Verification error: {e}")
            return None
    
    def get_jwks(self) -> Dict[str, Any]:
        """
        Get public key in JWKS (JSON Web Key Set) format.
        
        Returns:
            JWKS document with our public key
        """
        # Get public key numbers
        public_numbers = self.public_key.public_numbers()
        
        # Convert to base64url encoding
        def int_to_base64url(num: int) -> str:
            """Convert integer to base64url encoded string"""
            # Convert to bytes
            byte_length = (num.bit_length() + 7) // 8
            num_bytes = num.to_bytes(byte_length, byteorder='big')
            # Base64url encode
            return base64.urlsafe_b64encode(num_bytes).decode('ascii').rstrip('=')
        
        n = int_to_base64url(public_numbers.n)
        e = int_to_base64url(public_numbers.e)
        
        jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "kid": self.key_id,
                    "alg": "RS256",
                    "n": n,
                    "e": e,
                }
            ]
        }
        
        return jwks
    
    def get_public_key_pem(self) -> str:
        """
        Get public key in PEM format.
        
        Returns:
            PEM-encoded public key
        """
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')


# Global JWT key manager instance
jwt_key_manager = JWTKeyManager()

