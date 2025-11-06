# Chess Webapp with Google ADK Integration

This document explains the new chess webapp implementation with separate service architecture.

## 🎯 Overview

The chess webapp is a **completely separate service** from the existing MCP server, ensuring:
- ✅ Zero impact on ChatGPT widget integration
- ✅ Independent development and deployment
- ✅ Clean separation of concerns

## 🏗️ Architecture

### Three Independent Services

```
1. MCP Server (server/main.py)          [UNCHANGED]
   └─ Pure stdio MCP for ChatGPT

2. Webapp Backend (webapp-backend/)      [NEW]
   └─ FastAPI server on port 8001
   └─ Hosts ADK agent
   └─ Provides REST APIs

3. Webapp Frontend (webapp/)             [NEW]
   └─ React + TypeScript SPA
   └─ Runs on port 5173 (dev)
```

### Data Flow

```
User (Browser)
    ↓ HTTP
Webapp Backend (FastAPI :8001)
    ↓ Python imports
ADK Agent
    ↓ stdio subprocess
Chess MCP Server
    ↓
python-chess + Stockfish
```

## 📁 Directory Structure

```
ChessMCP/
├── agent/                    # ADK Agent Module
│   ├── agent.py             # Agent configuration
│   ├── requirements.txt     # ADK dependencies
│   ├── env.template         # Environment template
│   └── README.md
│
├── webapp-backend/          # Backend Service
│   ├── main.py             # FastAPI application
│   ├── agent_service.py    # Agent integration
│   ├── routes/
│   │   └── chat.py         # Chat endpoints
│   ├── requirements.txt
│   └── README.md
│
├── webapp/                  # Frontend Service
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # API client
│   │   ├── types/          # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
│
├── server/                  # MCP Server [UNCHANGED]
│   └── main.py             # Pure MCP for ChatGPT
│
└── src/, web/              # ChatGPT Widget [UNCHANGED]
```

## 🚀 Quick Start

### 1. Setup Agent

```bash
cd agent
pip install -r requirements.txt

# Create .env file with your Gemini API key
cp env.template .env
# Edit .env and add: GOOGLE_API_KEY=your_key_here
```

Get a Gemini API key from: https://aistudio.google.com/app/apikey

### 2. Setup Backend

```bash
cd webapp-backend
pip install -r requirements.txt
```

### 3. Setup Frontend

```bash
cd webapp
npm install
```

### 4. Run Everything

**Terminal 1 - Backend:**
```bash
cd webapp-backend
python3 main.py
# Runs on http://localhost:8001
```

**Terminal 2 - Frontend:**
```bash
cd webapp
npm run dev
# Runs on http://localhost:5173
```

**Terminal 3 - Test Agent (optional):**
```bash
cd agent
python3 agent.py
# Interactive CLI for testing
```

### 5. Open Webapp

Visit: http://localhost:5173

## 🎮 Features

### Chess Board
- Drag-and-drop pieces to make moves
- Visual feedback for legal moves
- Game status display (check, checkmate, etc.)
- New game button

### Side Panel - Two Tabs

**Moves Tab:**
- Move history in algebraic notation
- Move number tracking
- Scrollable list

**Chat Tab:**
- Chat with ADK agent
- AI assistant helps with:
  - Making moves
  - Position analysis
  - Strategic advice
  - Chess puzzles
  - Stockfish engine analysis

### Example Interactions

```
User: "Let's play chess! I'll start with e4"
Agent: [Makes move and explains]

User: "What's the best move in this position?"
Agent: [Analyzes and suggests]

User: "Show me a chess puzzle"
Agent: [Loads puzzle via MCP]

User: "Analyze this position with Stockfish"
Agent: [Uses chess_stockfish tool]
```

## 🔧 Development

### Hot Reload

Both frontend and backend support hot reload:
- Frontend: Vite watches for file changes
- Backend: Restart manually (or use uvicorn --reload)

### API Documentation

When backend is running, visit:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### Testing Agent Directly

```bash
cd agent
python3 agent.py

# Interactive CLI:
You: Let's play chess! e4
Agent: [Response from MCP]
```

## 📦 Production Deployment

### Option 1: Single Service

Build frontend and serve from backend:

```bash
# Build frontend
cd webapp
npm run build
# Output: webapp/dist/

# Start backend (serves both API and static files)
cd ../webapp-backend
# Uncomment static file serving in main.py
python3 main.py
```

### Option 2: Separate Services

- Deploy backend on Railway/Render/Cloud Run
- Deploy frontend on Vercel/Netlify
- Configure CORS and API URL

## 🧪 Testing

### Test Checklist

**Frontend:**
- [ ] Webapp loads in browser
- [ ] Can drag-drop pieces
- [ ] Move history displays correctly
- [ ] Chat tab opens and sends messages
- [ ] Moves tab shows game progress

**Backend:**
- [ ] Health check: `curl http://localhost:8001/health`
- [ ] API docs accessible: http://localhost:8001/docs
- [ ] Chat endpoint responds correctly

**Integration:**
- [ ] Message sent from chat reaches agent
- [ ] Agent makes chess moves via MCP
- [ ] Move updates reflected on board
- [ ] Full game playable

**Isolation:**
- [ ] ChatGPT widget still works (server/main.py unchanged)
- [ ] Can run webapp and ChatGPT widget simultaneously

## 🔒 Environment Variables

### agent/.env
```bash
GOOGLE_API_KEY=your_gemini_api_key
```

### webapp-backend/.env (optional)
```bash
PORT=8001
HOST=0.0.0.0
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Make sure agent dependencies are installed
cd agent
pip install -r requirements.txt

# Check if port is available
lsof -i :8001
```

### Frontend can't connect to backend
```bash
# Verify backend is running
curl http://localhost:8001/health

# Check Vite proxy config in webapp/vite.config.ts
```

### Agent fails to connect to MCP
```bash
# Test MCP server directly
cd server
python3 main.py
# Should start stdio MCP server

# Verify path in agent/agent.py:
# MCP_SERVER_PATH = Path(__file__).parent.parent / "server" / "main.py"
```

### Missing Gemini API key
```bash
# Create agent/.env file
cd agent
cp env.template .env
# Edit .env and add your key
```

## 📚 API Reference

### POST /api/chat/message
Send a message to the ADK agent.

**Request:**
```json
{
  "message": "Let's play chess! e4",
  "session_id": "user-123"
}
```

**Response:**
```json
{
  "response": "Great move! I'll respond with e5...",
  "metadata": {},
  "success": true
}
```

### GET /api/chat/health
Health check for chat service.

### POST /api/chat/reset
Reset conversation session.

## 🎨 UI Components

### ChessBoard
- Uses `react-chessboard` library
- Lichess color scheme
- Drag-and-drop enabled

### SidePanel
- Tab switching (Moves/Chat)
- Responsive design
- Scrollable content

### ChatTab
- Message list with auto-scroll
- Input field with send button
- Loading indicator
- Error handling

### MovesTab
- Move history in pairs (white, black)
- Move numbers
- Total move count

## 🔗 Related Documentation

- [Agent README](agent/README.md)
- [Backend README](webapp-backend/README.md)
- [Frontend README](webapp/README.md)
- [Main Project README](README.md)

## ⚠️ Important Notes

1. **MCP Server Unchanged**: The existing `server/main.py` has **zero modifications**. The ChatGPT widget continues to work exactly as before.

2. **Separate Services**: The webapp and ChatGPT widget are completely independent. You can use both simultaneously without conflicts.

3. **Port Configuration**:
   - MCP Server: stdio (no port)
   - Webapp Backend: 8001
   - Webapp Frontend: 5173 (dev)

4. **ADK Agent**: The agent spawns the MCP server as a subprocess, just like how Cursor or Claude Desktop connects to MCP servers.

## 🎯 Next Steps

1. Add user authentication
2. Implement session persistence
3. Add more chess features (puzzles, analysis board)
4. Deploy to production
5. Add multiplayer support

## 📝 License

MIT - Same as main project

