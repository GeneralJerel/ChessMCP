# Environment Variables Template

Create a `.env` file in the `server/` directory with these variables:

```bash
# Google OAuth 2.0 Credentials
# Get these from: https://console.cloud.google.com/apis/credentials
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# MCP Server URL
# In development with ngrok: https://your-subdomain.ngrok-free.app
# In production: https://your-domain.com
MCP_SERVER_URL=http://localhost:8000

# Optional: Stockfish path (if different from default)
# STOCKFISH_PATH=/opt/homebrew/bin/stockfish
```

## Setup Instructions

1. Copy this content to `server/.env`
2. Replace `your_google_client_id_here` with your actual Google OAuth Client ID
3. Replace `your_google_client_secret_here` with your actual Google OAuth Client Secret
4. Update `MCP_SERVER_URL` with your ngrok URL when testing with ChatGPT

