# Chess Webapp Backend

FastAPI backend for the chess webapp that integrates with the Google ADK agent.

## Features

- REST API for chess chat with ADK agent
- Session management for multiple users
- Static file serving for production deployment
- CORS support for development

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure the agent module is set up:
```bash
cd ../agent
pip install -r requirements.txt
```

3. Set up environment variables (optional):
```bash
cp env.template .env
# Edit .env if needed
```

## Running

Development mode:
```bash
python3 main.py
```

The server will start on http://localhost:8001

API documentation available at: http://localhost:8001/docs

## API Endpoints

### Chat

- `POST /api/chat/message` - Send message to agent
  ```json
  {
    "message": "Let's play chess! I'll move e4",
    "session_id": "user-123"
  }
  ```

- `GET /api/chat/health` - Health check
- `POST /api/chat/reset` - Reset conversation session

### General

- `GET /` - API info
- `GET /health` - Health check

## Architecture

```
Frontend (React)
    ↓ HTTP
Webapp Backend (FastAPI)
    ↓ Python imports
ADK Agent
    ↓ stdio
Chess MCP Server
```

## Development

The backend automatically reloads when you make changes. For production deployment:

1. Build the frontend: `cd ../webapp && npm run build`
2. Uncomment the static file serving in `main.py`
3. Deploy to your hosting platform

## Environment Variables

- `PORT` - Server port (default: 8001)
- `HOST` - Server host (default: 0.0.0.0)
- `GOOGLE_API_KEY` - Gemini API key (inherited from agent)

