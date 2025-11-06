# Chess MCP Client - Local Testing

A simple CLI client to test your Chess MCP server locally without needing ChatGPT.

## Quick Start

### 1. Start the Server

In one terminal:
```bash
cd /Users/jerel/Documents/Projects/ChessMCP/server
python3 main.py
```

### 2. Start the Client

In another terminal:
```bash
cd /Users/jerel/Documents/Projects/ChessMCP
python3 chess_client.py
```

You should see:
```
🔌 Connecting to Chess MCP Server at http://localhost:8000
✅ Server is online
============================================================
♟️  Chess MCP Client - Interactive Mode
============================================================
📊 Getting game status...
♟️ Game in Progress
🎯 You (White) to move
📊 Move 1
...
```

## Available Commands

### Make Moves
```
move e4
move Nf3
move O-O
move e8=Q
```

### Check Status
```
status
```

### Reset Game
```
reset
```

### Load Puzzle
```
puzzle easy
puzzle medium
puzzle hard
```

### Get Analysis
```
stockfish
stockfish 20
```

### Other Commands
```
tools       # List all available tools
help        # Show help
quit        # Exit
```

## Example Game Session

```
♟️  > move e4
♟️  Making move: e4
✅ Move played: e4
   FEN: rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1
   Turn: black
   Status: ongoing

♟️  > move e5
♟️  Making move: e5
✅ Move played: e5
   FEN: rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2
   Turn: white
   Status: ongoing

♟️  > stockfish
🤖 Getting Stockfish analysis (depth 15)...
✅ Stockfish recommends: Nf3 (Evaluation: +0.25)

♟️  > move Nf3
♟️  Making move: Nf3
✅ Move played: Nf3
   ...

♟️  > status
📊 Getting game status...
♟️ Game in Progress
🎯 Opponent (Black) to move
📊 Move 2
👥 Players:
   White: You
   Black: Opponent
📝 Last 3 moves: e4, e5, Nf3

♟️  > quit
👋 Goodbye! Thanks for playing!
```

## Connecting to Remote Server

You can also connect to your ngrok server for testing:

```bash
python3 chess_client.py https://shimmery-genevive-wooly.ngrok-free.dev
```

**Note:** This bypasses OAuth since it's a direct HTTP connection. For OAuth-protected servers, you'd need to add authentication headers.

## Features

✅ **No OAuth Required** - Bypasses authentication middleware for local testing  
✅ **Interactive CLI** - Simple command-line interface  
✅ **All 5 Tools** - Access all chess MCP tools  
✅ **Real-time Testing** - Test changes without ChatGPT  
✅ **Error Handling** - Shows clear error messages  

## Troubleshooting

### "Cannot connect to server"

**Solution:** Make sure the server is running:
```bash
cd server
python3 main.py
```

### "404 Not Found"

**Solution:** Server might be using a different MCP endpoint. Try:
- Check server logs for the correct endpoint
- Verify FastMCP is configured for HTTP

### "Authentication required"

If the server requires OAuth even for `/mcp` endpoint:

1. **Option A:** Temporarily disable auth middleware for local testing
2. **Option B:** Add `/mcp` to `UNAUTHENTICATED_PATHS` in `auth_middleware.py`

The `/mcp` endpoint should already be unauthenticated based on our configuration.

## Development Tips

- Use this client to quickly test changes
- Verify tool responses before deploying
- Test error handling
- Validate move logic
- Check game state persistence

## Advanced: Add Authentication

If you want to test with OAuth:

```python
# Add Bearer token to requests
headers = {
    "Authorization": f"Bearer {your_jwt_token}",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
```

---

**Have fun testing locally!** ♟️🎮

