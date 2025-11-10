# ChatGPT Connector Troubleshooting Guide

## Issue: "Doesn't support RFC 7591 Dynamic Client Registration"

This error occurs when ChatGPT has cached old OAuth metadata that pointed to `http://localhost:8000` instead of your ngrok URL.

## What Was Fixed

✅ **Added Cache-Control Headers** to all OAuth endpoints:
- `/.well-known/oauth-protected-resource`
- `/.well-known/oauth-authorization-server`
- `/.well-known/oauth-authorization-server/register`

✅ **Added Debug Logging** to track OAuth requests in real-time

✅ **Verified Endpoints** return correct ngrok URLs

## Steps to Resolve (REQUIRED)

### Step 1: Verify Your Server is Running with Correct URL

1. Make sure your server is running:
```bash
cd /Users/jerel/Documents/Projects/ChessMCP/server
python3 main.py
```

2. Verify ngrok is forwarding:
```bash
# In another terminal
ngrok http 8000
```

3. Check that `server/.env` has the correct ngrok URL:
```bash
cat server/.env | grep MCP_SERVER_URL
```

Should show: `MCP_SERVER_URL=https://shimmery-genevive-wooly.ngrok-free.dev` (or your current ngrok URL)

### Step 2: Test All OAuth Endpoints

Run these commands to verify everything is working:

```bash
# 1. Protected Resource Metadata
curl https://shimmery-genevive-wooly.ngrok-free.dev/.well-known/oauth-protected-resource

# Expected: Should show your ngrok URL in "resource" field

# 2. Authorization Server Metadata
curl https://shimmery-genevive-wooly.ngrok-free.dev/.well-known/oauth-authorization-server | jq .registration_endpoint

# Expected: "https://shimmery-genevive-wooly.ngrok-free.dev/.well-known/oauth-authorization-server/register"

# 3. DCR Endpoint
curl -X POST https://shimmery-genevive-wooly.ngrok-free.dev/.well-known/oauth-authorization-server/register \
  -H "Content-Type: application/json" \
  -d '{"redirect_uris":["https://chat.openai.com/aip/oauth2/callback"]}' | jq .client_id

# Expected: Your Google OAuth client ID
```

### Step 3: Clear ChatGPT's Cached Metadata (CRITICAL)

ChatGPT has cached the old metadata. You MUST do one of these:

**Option A: Delete and Recreate Connector (Recommended)**

1. Go to ChatGPT → Settings → Connectors
2. **Delete** the existing Chess MCP connector
3. **Wait 2-3 minutes** for cache to expire
4. **Create new connector**:
   - URL: `https://shimmery-genevive-wooly.ngrok-free.dev`
   - Name: Chess MCP
   - Description: Play chess with OAuth authentication

**Option B: Use Incognito/Private Browser**

1. Open ChatGPT in a **new incognito/private window**
2. Add the connector (fresh session, no cache)
3. Test there first

**Option C: Get New ngrok URL**

1. Stop ngrok (Ctrl+C)
2. Run `ngrok http 8000` again (gets new subdomain)
3. Update `server/.env` with the NEW ngrok URL
4. Restart Python server
5. Add connector with new URL (no cache exists)

### Step 4: Verify OAuth Flow

After recreating the connector:

1. In ChatGPT, try: `Let's play chess! I'll start with e4`
2. ChatGPT should prompt you to "Connect" or "Authenticate"
3. Click the authentication button
4. You'll be redirected to Google login
5. After authentication, you'll return to ChatGPT
6. The chess tool should work!

## Monitoring Logs

When you restart your server, you'll see OAuth debug logs:

```
[OAuth] Protected resource metadata requested from xxx.xxx.xxx.xxx
[OAuth] Authorization server metadata requested from xxx.xxx.xxx.xxx
[OAuth] Returning registration_endpoint: https://shimmery-genevive-wooly.ngrok-free.dev/...
[OAuth] DCR registration request received from xxx.xxx.xxx.xxx
[OAuth] DCR returning client_id: 656546278993-j77tahcn...
```

These logs help you confirm ChatGPT is accessing the endpoints.

## Common Issues

### "Still getting the same error"

**Cause:** ChatGPT is still using cached metadata

**Solution:** 
1. Make sure you deleted the old connector
2. Wait the full 2-3 minutes
3. Try Option B or C above

### "Endpoints return localhost:8000"

**Cause:** `server/.env` not updated or server not restarted

**Solution:**
```bash
# Update .env
echo "MCP_SERVER_URL=https://your-ngrok-url.ngrok-free.dev" > server/.env

# Restart server
python3 server/main.py
```

### "ngrok URL keeps changing"

**Cause:** Free ngrok generates new URLs on each restart

**Solutions:**
1. Keep ngrok running (don't restart it)
2. Use ngrok paid plan for static domain
3. Update `.env` and recreate connector each time URL changes

### "OAuth flow starts but fails"

**Cause:** Google OAuth redirect URIs not configured

**Solution:** Add this to Google Cloud Console:
- Redirect URI: `https://chat.openai.com/aip/oauth2/callback`

## Verification Checklist

Before adding connector in ChatGPT:

- [ ] Server running (`python3 main.py`)
- [ ] ngrok forwarding to port 8000
- [ ] `.env` has correct ngrok URL (no trailing slash)
- [ ] Protected resource endpoint returns ngrok URL
- [ ] Authorization server metadata returns ngrok URL in `registration_endpoint`
- [ ] DCR endpoint returns client credentials
- [ ] All responses include `Cache-Control: no-cache` headers
- [ ] Old connector deleted from ChatGPT
- [ ] Waited 2-3 minutes after deletion

## Success Indicators

You'll know it's working when:

1. ✅ All curl tests return correct ngrok URLs
2. ✅ Server logs show OAuth requests from ChatGPT's IP
3. ✅ Connector adds successfully (no RFC 7591 error)
4. ✅ Authentication prompt appears when using chess tools
5. ✅ Google login completes successfully
6. ✅ Chess moves work with your authenticated account

## Need Help?

If issues persist after following all steps:

1. Check server logs for errors
2. Verify Google OAuth credentials are correct in `.env`
3. Ensure ngrok URL in `.env` matches actual ngrok forwarding URL
4. Try the "new ngrok URL" option (Option C)
5. Verify Google Cloud Console has correct redirect URI

## Architecture Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  ChatGPT    │────▶│    ngrok     │────▶│  Your Server    │
│  (Client)   │     │   Tunnel     │     │  localhost:8000 │
└─────────────┘     └──────────────┘     └─────────────────┘
      │                                           │
      │                                           │
      └──────────────────────┐    ┌──────────────┘
                             ▼    ▼
                     ┌──────────────────┐
                     │  Google OAuth    │
                     │  (Auth Server)   │
                     └──────────────────┘
```

## Cache-Control Headers Now Added

All OAuth endpoints now return these headers to prevent caching:

```
Cache-Control: no-cache, no-store, must-revalidate
Pragma: no-cache
Expires: 0
```

This ensures ChatGPT always fetches fresh metadata.

---

**Last Updated:** After adding cache-control headers and debug logging  
**Status:** Ready for testing - follow Step 3 to clear ChatGPT cache

