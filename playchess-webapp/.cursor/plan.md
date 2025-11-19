# Build Full OAuth 2.1 Authorization Server Proxy

## Overview

Implement a complete OAuth 2.1 authorization server that wraps Google OAuth, generating our own client IDs and tokens that ChatGPT will accept. This replaces the simple credential-passthrough approach with a proper spec-compliant authorization server.

## Architecture Change

### Current (Broken)
```
ChatGPT → DCR → Return Google's client_id → ❌ ChatGPT rejects (wrong domain)
```

### New (Working)
```
ChatGPT → DCR → Generate our own client_id → ✅ ChatGPT accepts
        ↓
Authorization → Proxy to Google with our Google client_id
        ↓
Token Exchange → Get Google token → Issue our own JWT → ✅ ChatGPT uses
        ↓
MCP Request → Verify our JWT → Extract user → Access granted
```

## Implementation Steps

### 1. Create Client Registration Store

**New file: `server/client_store.py`**

Generate and store dynamic client registrations:
- Generate client IDs in format: `chess-mcp-{random_uuid}`
- Store mapping: our_client_id → {redirect_uris, created_at, metadata}
- In-memory storage (dict) for simplicity
- Thread-safe access with locks

```python
import uuid
from typing import Dict, Optional
from dataclasses import dataclass
import threading

@dataclass
class ClientRegistration:
    client_id: str
    client_secret: str
    redirect_uris: list
    created_at: str
    metadata: dict

class ClientStore:
    def __init__(self):
        self._clients: Dict[str, ClientRegistration] = {}
        self._lock = threading.Lock()
    
    def register_client(self, redirect_uris: list) -> ClientRegistration:
        client_id = f"chess-mcp-{uuid.uuid4().hex[:16]}"
        client_secret = f"secret-{uuid.uuid4().hex}"
        # ... store and return
```

### 2. Update DCR Endpoint to Generate Client IDs

**File: `server/main.py`**

Modify `dynamic_client_registration()`:
- Generate unique client_id for each ChatGPT registration
- Store in ClientStore
- Return our client credentials (not Google's)
- Follow RFC 7591 response format

```python
registration = client_store.register_client(body.get("redirect_uris", []))
response_data = {
    "client_id": registration.client_id,
    "client_secret": registration.client_secret,
    "redirect_uris": registration.redirect_uris,
    # ...
}
```

### 3. Create Authorization Endpoint Proxy

**New file: `server/oauth_proxy.py`**

Proxy authorization requests to Google:
- Accept authorization requests from ChatGPT
- Validate client_id from our ClientStore
- Map our client_id → Google's client_id
- Proxy to Google OAuth authorization endpoint
- Store state mapping for callback
- Redirect user to Google login

```python
async def authorization_proxy(request: Request):
    # Extract client_id from ChatGPT
    client_id = request.query_params.get("client_id")
    
    # Validate it's one we issued
    client = client_store.get_client(client_id)
    
    # Build Google OAuth URL with OUR Google client_id
    google_auth_url = build_google_auth_url(
        client_id=GOOGLE_CLIENT_ID,  # Use Google's
        redirect_uri=OUR_CALLBACK_URL,
        state=encode_state(chatgpt_state, our_client_id),
        # ... PKCE params
    )
    
    return RedirectResponse(google_auth_url)
```

### 4. Create OAuth Callback Handler

**File: `server/oauth_proxy.py`**

Handle Google OAuth callback:
- Receive authorization code from Google
- Decode state to get original ChatGPT client_id
- Exchange code for Google access token
- Generate OUR JWT token
- Redirect back to ChatGPT callback with our auth code

```python
async def oauth_callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    
    # Exchange code for Google token
    google_token = exchange_code_with_google(code)
    
    # Generate our authorization code
    our_auth_code = generate_auth_code(google_token, state)
    
    # Decode state to get ChatGPT redirect_uri
    chatgpt_redirect = decode_state(state).redirect_uri
    
    # Redirect to ChatGPT
    return RedirectResponse(f"{chatgpt_redirect}?code={our_auth_code}&state={state}")
```

### 5. Create Token Exchange Endpoint

**File: `server/oauth_proxy.py`**

Exchange authorization codes for access tokens:
- Accept token requests from ChatGPT
- Validate client credentials (our client_id/secret)
- Retrieve stored Google token from auth code
- Generate JWT access token signed with our keys
- Include user info in JWT claims
- Return token to ChatGPT

```python
async def token_endpoint(request: Request):
    form = await request.form()
    
    # Validate our client credentials
    client_id = form.get("client_id")
    client_secret = form.get("client_secret")
    client_store.validate_client(client_id, client_secret)
    
    # Get authorization code
    code = form.get("code")
    google_token = auth_code_store.exchange(code)
    
    # Get user info from Google token
    user_info = get_google_userinfo(google_token)
    
    # Generate OUR JWT
    access_token = generate_jwt(
        subject=user_info["sub"],
        email=user_info["email"],
        issuer=MCP_SERVER_URL,
        audience=MCP_SERVER_URL,
    )
    
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
    }
```

### 6. Generate RSA Key Pair for JWT Signing

**New file: `server/jwt_keys.py`**

Create and manage RSA keys for JWT signing:
- Generate RSA key pair on startup (or load from file)
- Sign JWTs with private key
- Publish public key via JWKS endpoint
- Handle key rotation (future enhancement)

```python
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
import json

class JWTKeyManager:
    def __init__(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
    
    def sign_jwt(self, payload: dict) -> str:
        return jwt.encode(payload, self.private_key, algorithm="RS256")
    
    def get_jwks(self) -> dict:
        # Convert public key to JWKS format
        # ...
```

### 7. Create JWKS Endpoint

**File: `server/main.py`**

Publish our public keys for JWT verification:
- Add route: `GET /oauth/jwks.json`
- Return public key in JWKS format
- ChatGPT and our middleware will use this to verify JWTs

```python
async def jwks_endpoint(request: Request):
    return JSONResponse(content=jwt_key_manager.get_jwks())
```

### 8. Update Authorization Server Metadata

**File: `server/main.py`**

Change metadata to point to OUR endpoints (not Google's):
- `issuer`: Our server URL
- `authorization_endpoint`: Our proxy endpoint
- `token_endpoint`: Our token exchange endpoint
- `jwks_uri`: Our JWKS endpoint
- `registration_endpoint`: Our DCR endpoint

```python
metadata = {
    "issuer": oauth_config.MCP_SERVER_URL,
    "authorization_endpoint": f"{oauth_config.MCP_SERVER_URL}/oauth/authorize",
    "token_endpoint": f"{oauth_config.MCP_SERVER_URL}/oauth/token",
    "jwks_uri": f"{oauth_config.MCP_SERVER_URL}/oauth/jwks.json",
    "registration_endpoint": f"{oauth_config.MCP_SERVER_URL}/.well-known/oauth-authorization-server/register",
    "code_challenge_methods_supported": ["S256"],
    "scopes_supported": ["openid", "email", "profile"],
}
```

### 9. Update Token Verification

**File: `server/auth_middleware.py`**

Verify OUR JWTs instead of Google's:
- Fetch public keys from our JWKS endpoint (not Google's)
- Validate issuer is our server URL (not Google)
- Validate audience is our server URL (not Google client_id)
- Extract user info from our JWT claims

```python
def verify_our_token(token: str) -> Optional[Dict[str, Any]]:
    # Use our JWKS, not Google's
    jwks = get_our_public_keys()  # From /oauth/jwks.json
    
    payload = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience=oauth_config.MCP_SERVER_URL,  # Our URL
        issuer=oauth_config.MCP_SERVER_URL,     # Our URL
    )
    return payload
```

### 10. Create Authorization Code Store

**New file: `server/auth_code_store.py`**

Manage authorization code lifecycle:
- Generate authorization codes
- Store mapping: auth_code → {google_token, user_info, client_id, expiry}
- Auto-expire codes after 5 minutes
- Validate PKCE code_verifier

```python
class AuthCodeStore:
    def generate_code(self, google_token: str, user_info: dict, 
                     client_id: str, code_challenge: str) -> str:
        code = f"code_{uuid.uuid4().hex}"
        self._codes[code] = {
            "google_token": google_token,
            "user_info": user_info,
            "client_id": client_id,
            "code_challenge": code_challenge,
            "expires_at": time.time() + 300  # 5 minutes
        }
        return code
```

### 11. Add All Proxy Routes

**File: `server/main.py`**

Add Starlette routes for OAuth proxy:
```python
oauth_routes = [
    # ... existing routes ...
    Route("/oauth/authorize", authorization_proxy, methods=["GET"]),
    Route("/oauth/callback", oauth_callback, methods=["GET"]),
    Route("/oauth/token", token_endpoint, methods=["POST"]),
    Route("/oauth/jwks.json", jwks_endpoint, methods=["GET"]),
]
```

### 12. Update Configuration

**File: `server/oauth_config.py`**

Add new configuration fields:
- OAuth callback URL for Google
- JWT signing settings
- Authorization code expiry
- Session state encryption key

### 13. Handle Google Redirect URI

**File: `server/.env.example` and `GOOGLE_OAUTH_SETUP.md`**

Update Google OAuth configuration:
- Redirect URI changes to: `https://your-ngrok-url.ngrok-free.dev/oauth/callback`
- Not ChatGPT's callback anymore (we handle that)

## Key Files to Create

1. `server/client_store.py` - DCR client storage
2. `server/auth_code_store.py` - Authorization code management
3. `server/jwt_keys.py` - RSA key management and JWT signing
4. `server/oauth_proxy.py` - Authorization and token proxy endpoints

## Key Files to Modify

1. `server/main.py` - Add proxy routes, update metadata
2. `server/oauth_config.py` - Add proxy configuration
3. `server/auth_middleware.py` - Verify our JWTs instead of Google's
4. `server/requirements.txt` - May need additional crypto libraries
5. `GOOGLE_OAUTH_SETUP.md` - Update redirect URI instructions

## OAuth Flow with Proxy

1. ChatGPT calls DCR → Get `chess-mcp-abc123` client_id ✅
2. ChatGPT → `/oauth/authorize?client_id=chess-mcp-abc123` 
3. Our server validates client, redirects to Google with OUR Google client_id
4. User authenticates with Google
5. Google → `/oauth/callback?code=google_code`
6. We exchange Google code for Google token
7. We generate our auth code, redirect to ChatGPT callback
8. ChatGPT → `/oauth/token` with our code + PKCE verifier
9. We validate, return OUR JWT (signed with our keys)
10. ChatGPT → MCP tools with our JWT
11. We verify our JWT, extract user, execute tool ✅

## Security Considerations

- Properly validate PKCE code_challenge/verifier
- Encrypt state parameter to prevent tampering
- Expire authorization codes after 5 minutes
- Expire access tokens after 1 hour
- Store Google refresh tokens for token refresh
- Validate redirect URIs against registered values
- Use secure random for ID generation

## Testing Strategy

1. Test each endpoint individually with curl
2. Test authorization flow manually in browser
3. Verify JWT signing and verification
4. Test with ChatGPT connector
5. Verify per-user isolation
6. Test token expiration handling

## Complexity Notes

This is a **major architectural change** that effectively builds a custom OAuth 2.1 authorization server. Estimated implementation:
- 5-6 new files
- ~500-700 lines of new code
- Requires careful testing of OAuth flows
- More complex debugging

## Alternative: Use Auth0/Stytch

Instead of building this ourselves, we could:
- Use Auth0 (supports DCR, Google social login)
- Use Stytch (MCP-compatible, supports DCR)
- Configure them to use Google as upstream identity provider
- Much simpler, production-ready

Would you like to proceed with the custom authorization server implementation, or explore using Auth0/Stytch instead?

