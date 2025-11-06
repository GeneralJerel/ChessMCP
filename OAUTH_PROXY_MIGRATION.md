# OAuth Proxy Migration Guide

## What Changed

The Chess MCP server has been upgraded from a simple Google OAuth passthrough to a **full OAuth 2.1 Authorization Server Proxy**. This fixes the "doesn't support RFC 7591 Dynamic Client Registration" error in ChatGPT.

## Why This Change Was Necessary

**Previous Architecture (Broken):**
```
ChatGPT → DCR → Returns Google client_id (*.apps.googleusercontent.com)
                ❌ ChatGPT rejects: domain mismatch
```

**New Architecture (Working):**
```
ChatGPT → DCR → Returns our client_id (chess-mcp-xxx)
        ↓
        Proxy → Google OAuth → Our JWT → ChatGPT ✅
```

## What's New

### 1. Full Authorization Server Proxy

**New Components:**
- `server/client_store.py` - Manages registered OAuth clients
- `server/auth_code_store.py` - Manages authorization codes with PKCE
- `server/jwt_keys.py` - RSA key management for JWT signing
- `server/oauth_proxy.py` - OAuth flow proxy endpoints

### 2. Our Own Client IDs

ChatGPT now receives client IDs like:
- `chess-mcp-a1b2c3d4e5f6g7h8` (our format)
- Not `*.apps.googleusercontent.com` (Google's format)

### 3. Our Own JWT Tokens

We now issue JWT tokens signed with our own RSA keys:
```json
{
  "iss": "https://your-server.ngrok-free.dev",
  "aud": "https://your-server.ngrok-free.dev",
  "sub": "google_user_id",
  "email": "user@gmail.com",
  "scope": "openid email profile"
}
```

### 4. New OAuth Endpoints

Added proxy endpoints:
- `/oauth/authorize` - Authorization request handler
- `/oauth/callback` - Google OAuth callback
- `/oauth/token` - Token exchange endpoint
- `/oauth/jwks.json` - Public key publication

### 5. Updated Metadata

Authorization server metadata now points to our endpoints:
```json
{
  "issuer": "https://your-server.ngrok-free.dev",
  "authorization_endpoint": "https://your-server.ngrok-free.dev/oauth/authorize",
  "token_endpoint": "https://your-server.ngrok-free.dev/oauth/token",
  "jwks_uri": "https://your-server.ngrok-free.dev/oauth/jwks.json"
}
```

## Migration Steps

### Step 1: Update Google OAuth Redirect URI

**CRITICAL:** The redirect URI has changed!

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Click on your OAuth 2.0 Client ID
3. Under **Authorized redirect URIs**, **remove** old URI and **add**:
   ```
   https://your-ngrok-url.ngrok-free.dev/oauth/callback
   ```
   (Replace with your actual ngrok URL)

**Before (old):**
- ❌ `https://chat.openai.com/aip/oauth2/callback`

**After (new):**
- ✅ `https://your-ngrok-url.ngrok-free.dev/oauth/callback`

4. Click **Save**

### Step 2: Ensure .env is Correct

Your `server/.env` should have:
```bash
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
MCP_SERVER_URL=https://your-ngrok-url.ngrok-free.dev
```

### Step 3: Restart Server

```bash
cd /Users/jerel/Documents/Projects/ChessMCP/server
python3 main.py
```

You should see:
```
[JWTKeyManager] Generated RSA key pair with kid: chess-mcp-key-1
============================================================
Chess MCP Server with Google OAuth 2.1
============================================================
✓ OAuth configuration validated
...
OAuth Endpoints:
  - Authorization: https://your-server/oauth/authorize
  - Token: https://your-server/oauth/token
  - JWKS: https://your-server/oauth/jwks.json
  - DCR: https://your-server/.well-known/oauth-authorization-server/register
```

### Step 4: Test New Endpoints

```bash
# 1. Test authorization server metadata (should show our endpoints)
curl https://your-ngrok-url.ngrok-free.dev/.well-known/oauth-authorization-server | jq .

# 2. Test DCR (should return chess-mcp-* client_id)
curl -X POST https://your-ngrok-url.ngrok-free.dev/.well-known/oauth-authorization-server/register \
  -H "Content-Type: application/json" \
  -d '{"redirect_uris":["https://chat.openai.com/aip/oauth2/callback"]}' | jq .client_id

# 3. Test JWKS (should return our public key)
curl https://your-ngrok-url.ngrok-free.dev/oauth/jwks.json | jq .
```

Expected DCR response:
```json
{
  "client_id": "chess-mcp-a1b2c3d4e5f6g7h8",
  "client_secret": "secret-...",
  ...
}
```

### Step 5: Delete Old ChatGPT Connector

**IMPORTANT:** Delete the old connector and wait 2-3 minutes!

1. ChatGPT → Settings → Connectors
2. Delete "Chess MCP" connector
3. **Wait 2-3 minutes** for cache to clear

### Step 6: Add New Connector in ChatGPT

1. ChatGPT → Settings → Connectors → Add
2. URL: `https://your-ngrok-url.ngrok-free.dev`
3. Name: Chess MCP
4. Save

ChatGPT will now:
1. Discover our authorization server metadata ✅
2. Register via DCR and get `chess-mcp-*` client_id ✅
3. Initiate OAuth flow to our `/oauth/authorize` ✅
4. We proxy to Google, user authenticates ✅
5. Google calls our `/oauth/callback` ✅
6. We issue our own JWT and redirect to ChatGPT ✅
7. ChatGPT uses our JWT for MCP requests ✅

### Step 7: Test OAuth Flow

1. In ChatGPT: `Let's play chess! I'll start with e4`
2. Click "Connect" when prompted
3. Authenticate with Google
4. Should work! ♟️

## OAuth Flow Diagram (New)

```
┌──────────┐                     ┌──────────────────┐                  ┌─────────────┐
│ ChatGPT  │                     │  Our Auth Server │                  │   Google    │
│          │                     │  (Proxy Layer)   │                  │   OAuth     │
└────┬─────┘                     └────────┬─────────┘                  └──────┬──────┘
     │                                    │                                    │
     │ 1. DCR Request                     │                                    │
     ├───────────────────────────────────▶│                                    │
     │                                    │                                    │
     │◀───────────────────────────────────┤                                    │
     │ 2. client_id: chess-mcp-xxx        │                                    │
     │                                    │                                    │
     │ 3. /oauth/authorize                │                                    │
     ├───────────────────────────────────▶│                                    │
     │                                    │ 4. Redirect to Google              │
     │                                    ├───────────────────────────────────▶│
     │                                    │                                    │
     │                                    │◀───────────────────────────────────┤
     │                                    │ 5. User authenticates              │
     │                                    │                                    │
     │                                    │ 6. /oauth/callback?code=...        │
     │                                    │◀───────────────────────────────────┤
     │                                    │                                    │
     │                                    │ 7. Exchange code for Google token  │
     │                                    ├───────────────────────────────────▶│
     │                                    │                                    │
     │                                    │◀───────────────────────────────────┤
     │                                    │ 8. Google access token             │
     │                                    │                                    │
     │◀───────────────────────────────────┤                                    │
     │ 9. Redirect with our auth code     │                                    │
     │                                    │                                    │
     │ 10. /oauth/token (exchange code)   │                                    │
     ├───────────────────────────────────▶│                                    │
     │                                    │                                    │
     │◀───────────────────────────────────┤                                    │
     │ 11. Our JWT (signed with our key)  │                                    │
     │                                    │                                    │
     │ 12. MCP requests with our JWT      │                                    │
     ├───────────────────────────────────▶│                                    │
     │                                    │ (verifies our JWT)                 │
     │◀───────────────────────────────────┤                                    │
     │ 13. Chess tool responses           │                                    │
```

## Benefits

✅ **ChatGPT Compatible** - Issues client IDs that match our domain
✅ **RFC Compliant** - Full OAuth 2.1 + DCR implementation
✅ **Secure** - PKCE validation, token signing, proper JWT verification
✅ **Flexible** - Can add more identity providers in the future
✅ **Per-User** - Each user gets isolated game state

## Troubleshooting

### Error: "Invalid redirect URI" from Google

**Cause:** Redirect URI not updated in Google Console

**Solution:** Add `https://your-ngrok-url.ngrok-free.dev/oauth/callback` to Google OAuth settings

### Error: "Client not found" in logs

**Cause:** Client registration expired or server restarted

**Solution:** Delete and recreate connector in ChatGPT (triggers new DCR)

### Error: "Invalid authorization code"

**Cause:** Code expired (10 minute lifetime) or already used

**Solution:** Try authentication flow again

### Error: "Token verification failed"

**Cause:** JWT signed with different keys (server restarted)

**Solution:** RSA keys regenerate on server restart. User needs to re-authenticate.

## What You Need to Update

If you previously set up Google OAuth:

- [ ] Update Google OAuth redirect URI to `/oauth/callback`
- [ ] Delete old ChatGPT connector
- [ ] Wait 2-3 minutes
- [ ] Add new connector
- [ ] Test OAuth flow

## Production Considerations

For production deployment:

1. **Persist RSA keys** - Save to file/database to survive restarts
2. **Persistent storage** - Use Redis/PostgreSQL for client and code stores
3. **Token refresh** - Implement refresh token handling
4. **Key rotation** - Plan for periodic key rotation
5. **Monitoring** - Add metrics for OAuth flows
6. **Rate limiting** - Protect endpoints from abuse

## Support

See these guides for more help:
- `NEXT_STEPS.md` - What to do next
- `CHATGPT_CONNECTOR_TROUBLESHOOTING.md` - Common issues
- `OAUTH_QUICK_START.md` - Quick setup guide
- `GOOGLE_OAUTH_SETUP.md` - Detailed Google setup

