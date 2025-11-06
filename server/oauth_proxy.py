"""
OAuth 2.1 Authorization Server Proxy
Proxies OAuth flow to Google while issuing our own tokens
"""

import json
import base64
import secrets
import requests
from urllib.parse import urlencode, parse_qs
from typing import Optional, Dict, Any
from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse
from client_store import client_store
from auth_code_store import auth_code_store
from jwt_keys import jwt_key_manager
from oauth_config import oauth_config


def encode_state(data: dict) -> str:
    """
    Encode state parameter as base64 JSON.
    In production, encrypt this to prevent tampering.
    
    Args:
        data: Dictionary to encode
    
    Returns:
        Base64-encoded JSON string
    """
    json_str = json.dumps(data)
    return base64.urlsafe_b64encode(json_str.encode()).decode().rstrip('=')


def decode_state(state: str) -> Optional[dict]:
    """
    Decode state parameter from base64 JSON.
    
    Args:
        state: Base64-encoded state
    
    Returns:
        Decoded dictionary or None if invalid
    """
    try:
        # Add padding if needed
        padding = 4 - len(state) % 4
        if padding != 4:
            state += '=' * padding
        
        json_str = base64.urlsafe_b64decode(state.encode()).decode()
        return json.loads(json_str)
    except Exception as e:
        print(f"[OAuth] Error decoding state: {e}")
        return None


async def authorization_endpoint(request: Request):
    """
    OAuth 2.1 Authorization Endpoint (Proxy to Google)
    
    Handles authorization requests from ChatGPT and proxies to Google OAuth.
    """
    print(f"[OAuth] Authorization request from {request.client.host if request.client else 'unknown'}")
    
    try:
        # Extract OAuth parameters from ChatGPT
        client_id = request.query_params.get("client_id")
        redirect_uri = request.query_params.get("redirect_uri")
        state = request.query_params.get("state", "")
        scope = request.query_params.get("scope", "openid email profile")
        code_challenge = request.query_params.get("code_challenge")
        code_challenge_method = request.query_params.get("code_challenge_method", "S256")
        response_type = request.query_params.get("response_type", "code")
        
        print(f"[OAuth] Auth request - client_id: {client_id}, scope: {scope}")
        
        # Validate client_id
        client = client_store.get_client(client_id)
        if not client:
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_client", "error_description": "Unknown client_id"}
            )
        
        # Validate redirect_uri
        if not client_store.validate_redirect_uri(client_id, redirect_uri):
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_request", "error_description": "Invalid redirect_uri"}
            )
        
        # Validate PKCE
        if not code_challenge or code_challenge_method != "S256":
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_request", "error_description": "PKCE with S256 required"}
            )
        
        # Encode our state (preserve ChatGPT's state + our metadata)
        our_state = encode_state({
            "chatgpt_state": state,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "scope": scope,
        })
        
        # Build Google OAuth authorization URL
        google_auth_params = {
            "client_id": oauth_config.GOOGLE_CLIENT_ID,
            "redirect_uri": f"{oauth_config.MCP_SERVER_URL}/oauth/callback",
            "response_type": "code",
            "scope": "openid email profile",
            "state": our_state,
            "access_type": "offline",  # Get refresh token
            "prompt": "consent",  # Force consent screen
        }
        
        google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(google_auth_params)}"
        
        print(f"[OAuth] Redirecting to Google OAuth")
        
        # Redirect user to Google
        return RedirectResponse(url=google_auth_url, status_code=302)
    
    except Exception as e:
        print(f"[OAuth] Error in authorization endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "server_error", "error_description": str(e)}
        )


async def oauth_callback(request: Request):
    """
    OAuth Callback from Google
    
    Receives authorization code from Google, exchanges for tokens,
    then redirects back to ChatGPT with our authorization code.
    """
    print(f"[OAuth] Callback from Google")
    
    try:
        # Extract Google's response
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")
        
        if error:
            print(f"[OAuth] Google returned error: {error}")
            return JSONResponse(
                status_code=400,
                content={"error": error, "error_description": "Google OAuth error"}
            )
        
        if not code or not state:
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_request", "error_description": "Missing code or state"}
            )
        
        # Decode our state
        state_data = decode_state(state)
        if not state_data:
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_request", "error_description": "Invalid state parameter"}
            )
        
        chatgpt_client_id = state_data.get("client_id")
        chatgpt_redirect_uri = state_data.get("redirect_uri")
        chatgpt_state = state_data.get("chatgpt_state")
        code_challenge = state_data.get("code_challenge")
        code_challenge_method = state_data.get("code_challenge_method")
        scope = state_data.get("scope")
        
        print(f"[OAuth] Exchanging Google code for tokens")
        
        # Exchange Google authorization code for tokens
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": oauth_config.GOOGLE_CLIENT_ID,
                "client_secret": oauth_config.GOOGLE_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{oauth_config.MCP_SERVER_URL}/oauth/callback",
                "grant_type": "authorization_code",
            },
            timeout=10
        )
        
        if token_response.status_code != 200:
            print(f"[OAuth] Google token exchange failed: {token_response.text}")
            return JSONResponse(
                status_code=400,
                content={"error": "server_error", "error_description": "Failed to exchange code with Google"}
            )
        
        tokens = token_response.json()
        google_access_token = tokens.get("access_token")
        google_id_token = tokens.get("id_token")
        
        print(f"[OAuth] Got Google tokens, fetching user info")
        
        # Get user info from Google
        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"},
            timeout=10
        )
        
        if userinfo_response.status_code != 200:
            print(f"[OAuth] Failed to get user info: {userinfo_response.text}")
            return JSONResponse(
                status_code=400,
                content={"error": "server_error", "error_description": "Failed to get user info"}
            )
        
        user_info = userinfo_response.json()
        
        print(f"[OAuth] User authenticated: {user_info.get('email')}")
        
        # Create our authorization code
        our_code = auth_code_store.create_code(
            google_access_token=google_access_token,
            google_id_token=google_id_token,
            user_info=user_info,
            client_id=chatgpt_client_id,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            redirect_uri=chatgpt_redirect_uri,
            scope=scope
        )
        
        # Build redirect URL back to ChatGPT
        redirect_params = {
            "code": our_code,
            "state": chatgpt_state,
        }
        
        redirect_url = f"{chatgpt_redirect_uri}?{urlencode(redirect_params)}"
        
        print(f"[OAuth] Redirecting to ChatGPT callback")
        
        return RedirectResponse(url=redirect_url, status_code=302)
    
    except Exception as e:
        print(f"[OAuth] Error in callback: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "server_error", "error_description": str(e)}
        )


async def token_endpoint(request: Request):
    """
    OAuth 2.1 Token Endpoint
    
    Exchanges authorization codes for access tokens.
    Returns JWTs signed with our own keys.
    """
    print(f"[OAuth] Token exchange request from {request.client.host if request.client else 'unknown'}")
    
    try:
        # Parse form data
        form = await request.form()
        
        grant_type = form.get("grant_type")
        code = form.get("code")
        client_id = form.get("client_id")
        client_secret = form.get("client_secret")
        redirect_uri = form.get("redirect_uri")
        code_verifier = form.get("code_verifier")
        
        print(f"[OAuth] Token request - grant_type: {grant_type}, client_id: {client_id}")
        
        # Validate grant type
        if grant_type != "authorization_code":
            return JSONResponse(
                status_code=400,
                content={"error": "unsupported_grant_type", "error_description": "Only authorization_code supported"}
            )
        
        # Validate client credentials
        if not client_store.validate_client(client_id, client_secret):
            return JSONResponse(
                status_code=401,
                content={"error": "invalid_client", "error_description": "Invalid client credentials"}
            )
        
        # Exchange authorization code
        auth_code = auth_code_store.exchange_code(
            code=code,
            code_verifier=code_verifier,
            client_id=client_id,
            redirect_uri=redirect_uri
        )
        
        if not auth_code:
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_grant", "error_description": "Invalid or expired authorization code"}
            )
        
        # Extract user info
        user_info = auth_code.user_info
        
        print(f"[OAuth] Issuing JWT for user: {user_info.get('email')}")
        
        # Generate our JWT access token
        access_token = jwt_key_manager.sign_jwt(
            subject=user_info.get("sub"),
            email=user_info.get("email"),
            name=user_info.get("name", ""),
            issuer=oauth_config.MCP_SERVER_URL,
            audience=oauth_config.MCP_SERVER_URL,
            scope=auth_code.scope,
            expires_in=3600  # 1 hour
        )
        
        # Return token response
        response_data = {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": auth_code.scope,
        }
        
        # Optionally include ID token (same as access token for simplicity)
        response_data["id_token"] = access_token
        
        print(f"[OAuth] Token issued successfully")
        
        return JSONResponse(content=response_data)
    
    except Exception as e:
        print(f"[OAuth] Error in token endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "server_error", "error_description": str(e)}
        )


async def jwks_endpoint(request: Request):
    """
    JWKS (JSON Web Key Set) Endpoint
    
    Publishes our public key for JWT verification.
    """
    print(f"[OAuth] JWKS request from {request.client.host if request.client else 'unknown'}")
    
    jwks = jwt_key_manager.get_jwks()
    
    response = JSONResponse(content=jwks)
    
    # Add cache headers (can cache JWKS for a while)
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    return response

