# Google OAuth 2.0 Setup Guide for Chess MCP

This guide walks you through setting up Google OAuth 2.0 credentials for the Chess MCP server to enable ChatGPT authentication.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a Project** → **New Project**
3. Enter project name: `Chess MCP` (or your preferred name)
4. Click **Create**

## Step 2: Enable Required APIs

1. In your project, go to **APIs & Services** → **Library**
2. Search for and enable:
   - **Google+ API** (for userinfo access)
   - Or **Google Identity** (alternative for profile data)

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type (unless you have Google Workspace)
3. Click **Create**

### Fill in the consent screen details:

**App information:**
- App name: `Chess MCP`
- User support email: Your email
- App logo: (optional)

**App domain:**
- Application home page: `https://your-domain.com` (or leave blank for dev)
- Privacy policy: (optional for testing)
- Terms of service: (optional for testing)

**Developer contact:**
- Email addresses: Your email

4. Click **Save and Continue**

### Add Scopes:

1. Click **Add or Remove Scopes**
2. Select these scopes:
   - `openid`
   - `email`
   - `profile`
3. Click **Update** → **Save and Continue**

### Add Test Users (for development):

1. Click **Add Users**
2. Enter your Google email address
3. Click **Add** → **Save and Continue**

4. Review and go back to dashboard

## Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth 2.0 Client ID**

### Configure the OAuth client:

**Application type:** Web application

**Name:** `Chess MCP Server`

**Authorized JavaScript origins:**
- Add: `http://localhost:8000` (for local testing)
- Add: `https://your-ngrok-url.ngrok-free.app` (for ChatGPT testing)

**Authorized redirect URIs:**
- Add: `https://your-ngrok-url.ngrok-free.dev/oauth/callback` (replace with your actual ngrok URL)
- Add: `http://localhost:8000/oauth/callback` (for local testing)

5. Click **Create**

### Save Your Credentials:

A dialog will appear with:
- **Client ID**: `123456789-abcdef.apps.googleusercontent.com`
- **Client Secret**: `GOCSPX-abc123...`

**IMPORTANT:** Copy both values immediately!

## Step 5: Configure Chess MCP Server

1. Navigate to your Chess MCP server directory:
```bash
cd /Users/jerel/Documents/Projects/ChessMCP/server
```

2. Create a `.env` file:
```bash
nano .env
```

3. Add your credentials:
```bash
# Google OAuth 2.0 Credentials
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here

# MCP Server URL (update when using ngrok)
MCP_SERVER_URL=http://localhost:8000
```

4. Save the file (Ctrl+O, Enter, Ctrl+X in nano)

## Step 6: Install Dependencies

```bash
pip3 install -r requirements.txt
```

## Step 7: Test the Server Locally

```bash
cd /Users/jerel/Documents/Projects/ChessMCP/server
python3 main.py
```

You should see:
```
============================================================
Chess MCP Server with Google OAuth 2.1
============================================================
✓ OAuth configuration validated
✓ Server URL: http://localhost:8000
✓ Google Client ID: 123456789-abcdef...

OAuth Endpoints:
  - Protected Resource: http://localhost:8000/.well-known/oauth-protected-resource
  - Auth Server Metadata: http://localhost:8000/.well-known/oauth-authorization-server
  - DCR: http://localhost:8000/.well-known/oauth-authorization-server/register
  - Health: http://localhost:8000/health
============================================================
```

## Step 8: Test OAuth Endpoints

In a new terminal, test the endpoints:

```bash
# Health check
curl http://localhost:8000/health

# Protected resource metadata
curl http://localhost:8000/.well-known/oauth-protected-resource

# Authorization server metadata
curl http://localhost:8000/.well-known/oauth-authorization-server
```

## Step 9: Expose Server with ngrok

1. In a new terminal:
```bash
ngrok http 8000
```

2. Copy the HTTPS forwarding URL:
```
Forwarding    https://abc123.ngrok-free.app -> http://localhost:8000
```

3. Update your `.env` file:
```bash
MCP_SERVER_URL=https://abc123.ngrok-free.app
```

4. Restart the Chess MCP server

## Step 10: Update Google OAuth Redirect URIs

**IMPORTANT:** The redirect URI has changed to our OAuth callback endpoint.

1. Go back to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Click on your OAuth 2.0 Client ID
4. Under **Authorized redirect URIs**, update to:
   - `https://abc123.ngrok-free.app/oauth/callback` (replace with your actual ngrok URL)
   - Format: `https://YOUR-NGROK-SUBDOMAIN.ngrok-free.dev/oauth/callback`
5. Click **Save**

> **Note:** 
> - The redirect URI is now `/oauth/callback` (not ChatGPT's callback)
> - You need to update this every time ngrok generates a new URL (free tier)
> - Make sure the ngrok URL matches your `MCP_SERVER_URL` in `.env`

## Step 11: Configure ChatGPT

1. Go to [ChatGPT](https://chat.openai.com/)
2. Open **Settings** → **Connectors** (or **Beta Features**)
3. Click **Add Connector**

**Connector Details:**
- **Name:** Chess MCP
- **URL:** `https://abc123.ngrok-free.app` (your ngrok URL)
- **Description:** Play chess with interactive board and move validation

4. Click **Save**

ChatGPT will now:
1. Discover your OAuth metadata
2. Register as a client via DCR
3. Initiate OAuth flow when a user tries to use the connector
4. Redirect user to Google login
5. Receive access token
6. Make authenticated requests to your server

## Step 12: Test in ChatGPT

In a new ChatGPT conversation:

1. Type: `Let's play chess! I'll start with e4`
2. ChatGPT will prompt you to authenticate
3. Click **Connect** or **Authenticate**
4. You'll be redirected to Google login
5. Grant permissions (openid, email, profile)
6. You'll be redirected back to ChatGPT
7. The chess board should appear with your move!

## Troubleshooting

### Error: "OAuth configuration incomplete"

- Make sure `.env` file exists in `server/` directory
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set
- Check for typos or extra spaces

### Error: "Invalid redirect URI"

- Ensure ChatGPT's callback URL is in Google Console authorized redirect URIs
- The URL must exactly match: `https://chat.openai.com/aip/oauth2/callback`

### Error: "Access blocked: This app's request is invalid"

- Check that required scopes are added in Google OAuth consent screen
- Ensure you added yourself as a test user (for development)

### Error: "Token verification failed"

- Verify your Google Client ID matches the one in `.env`
- Check that tokens aren't expired
- Ensure server time is synchronized

### ChatGPT can't reach server

- Verify ngrok is running and forwarding to port 8000
- Check that `MCP_SERVER_URL` in `.env` matches ngrok URL
- Test endpoints with curl to confirm they're accessible

## Security Notes

- **Never commit `.env` file to git** (it's in .gitignore)
- **Keep Client Secret secure** - treat it like a password
- For production, use a real domain instead of ngrok
- Consider implementing rate limiting and monitoring
- Rotate credentials periodically

## Production Deployment

For production use:

1. Deploy server to a cloud provider (AWS, GCP, Azure, etc.)
2. Get a real domain name and SSL certificate
3. Update `MCP_SERVER_URL` to your production domain
4. Update Google OAuth redirect URIs with production URLs
5. Set OAuth consent screen to "Published" status
6. Implement proper logging and monitoring
7. Set up token refresh handling
8. Consider adding user session management
9. Implement rate limiting

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [MCP Authorization Spec](https://spec.modelcontextprotocol.io/specification/2025-06-18/authorization/)
- [OAuth 2.1 Draft Spec](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-13)
- [RFC 9728: Protected Resource Metadata](https://datatracker.ietf.org/doc/html/rfc9728)

## Support

If you encounter issues:
1. Check server logs for error messages
2. Verify all environment variables are set correctly
3. Test OAuth endpoints with curl
4. Check ngrok web interface at http://127.0.0.1:4040
5. Review Google Cloud Console logs

