# OAuth Quick Start Guide

Get Chess MCP working with Google OAuth in 5 minutes!

## Prerequisites

- Google account
- ngrok installed (`brew install ngrok`)
- Python 3.8+

## Quick Setup

### 1. Get Google OAuth Credentials (2 min)

1. Go to https://console.cloud.google.com/apis/credentials
2. Create project → Enable Google+ API
3. Create OAuth 2.0 Client ID (Web application)
4. Add redirect URI: `https://chat.openai.com/aip/oauth2/callback`
5. Copy Client ID and Secret

### 2. Configure Server (1 min)

```bash
cd server
cat > .env << EOF
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
MCP_SERVER_URL=http://localhost:8000
EOF
```

Replace `your_client_id_here` and `your_client_secret_here` with your actual credentials.

### 3. Install & Start (2 min)

```bash
# Install dependencies
pip3 install -r requirements.txt

# Start server
python3 main.py
```

In another terminal:
```bash
# Expose with ngrok
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)
```

Update `.env`:
```bash
MCP_SERVER_URL=https://abc123.ngrok-free.app
```

Restart server.

### 4. Connect in ChatGPT (30 sec)

**IMPORTANT:** If you previously added the connector, DELETE it first and wait 2-3 minutes!

1. ChatGPT → Settings → Connectors
2. If Chess MCP exists, **delete it and wait 2-3 minutes**
3. Click **Add Connector**
4. URL: `https://abc123.ngrok-free.app` (your ngrok URL)
5. Name: Chess MCP
6. Save

### 5. Play Chess!

In ChatGPT:
```
Let's play chess! I'll start with e4
```

ChatGPT will ask to connect → Authenticate with Google → Play!

## Verify Setup

Test endpoints:
```bash
curl https://YOUR-NGROK-URL.ngrok-free.app/health
curl https://YOUR-NGROK-URL.ngrok-free.app/.well-known/oauth-protected-resource
```

## Common Issues

**"OAuth configuration incomplete"**
→ Check `.env` file has all values

**"Invalid redirect URI"**
→ Add `https://chat.openai.com/aip/oauth2/callback` to Google Console

**ChatGPT can't connect**
→ Verify ngrok URL in `.env` and server is running

## Full Documentation

See [GOOGLE_OAUTH_SETUP.md](./GOOGLE_OAUTH_SETUP.md) for detailed instructions.

