# Chess ADK Agent

This directory contains the Google ADK agent that provides chess assistance by connecting to the Chess MCP server.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your Gemini API key:
```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

3. Get a Gemini API key from: https://aistudio.google.com/app/apikey

## Testing

Run the agent in interactive CLI mode:

```bash
python3 agent.py
```

This allows you to test the agent's chess capabilities directly without the webapp.

## Usage in Webapp Backend

The webapp backend imports and uses this agent:

```python
from agent import get_agent, chat_with_agent

# Get agent instance
agent = get_agent()

# Chat with agent
result = await chat_with_agent("Let's play chess! I'll start with e4")
print(result["response"])
```

## How It Works

1. The agent uses `StdioMCPClient` to spawn the Chess MCP server as a subprocess
2. The MCP server provides chess tools: `chess_move`, `chess_status`, `chess_stockfish`, etc.
3. The ADK agent uses these tools to help users play chess
4. Communication flow: User → Agent → MCP Tools → Chess Logic → Response

## Architecture

```
User Message
    ↓
ADK Agent (Gemini)
    ↓
MCP Client (stdio)
    ↓
Chess MCP Server
    ↓
python-chess + Stockfish
    ↓
Response
```

