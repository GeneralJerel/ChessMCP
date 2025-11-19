# Local Chess MCP Testing Guide

Play chess locally without ChatGPT using the built-in test client!

## Quick Start

```bash
cd /Users/jerel/Documents/Projects/ChessMCP
python3 chess_local_test.py
```

That's it! You can now play chess in your terminal.

## Available Commands

### Playing Chess
```
move e4        # Pawn to e4
move Nf3       # Knight to f3
move O-O       # Castle kingside
move e8=Q      # Promote to queen
```

### Game Management
```
status         # Show current game state
reset          # Start new game
```

### Puzzles & Analysis
```
puzzle easy    # Load easy puzzle
puzzle medium  # Load medium puzzle  
puzzle hard    # Load hard puzzle
stockfish      # Get engine analysis (depth 15)
stockfish 20   # Get deeper analysis
```

### Other
```
help           # Show help
quit           # Exit
```

## Example Session

```
♟️  Chess MCP Local Tester
============================================================
📊 Initial game status...
✅ ♟️ Game in Progress
🎯 You (White) to move

♟️  > move e4
♟️  Making move: e4
✅ Move played: e4
   FEN: rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1
   Turn: black
   Status: ongoing

♟️  > move e5
♟️  Making move: e5
✅ Move played: e5

♟️  > stockfish
🤖 Stockfish analysis (depth 15)...
✅ Stockfish recommends: Nf3 (Evaluation: +0.25)

♟️  > move Nf3
✅ Move played: Nf3

♟️  > status
📊 Game status...
✅ ♟️ Game in Progress
🎯 Opponent (Black) to move
📊 Move 2
📝 Last 3 moves: e4, e5, Nf3

♟️  > puzzle hard
🧩 Loading hard puzzle...
✅ 🧩 Mate in 1 Puzzle (Hard)
White to move and checkmate in one move!
💡 Hint: The king cannot escape the back rank!

♟️  > quit
👋 Goodbye! Thanks for playing!
```

## How It Works

The local tester:
1. Imports chess functions directly from `server/main.py`
2. Sets up a mock user context (bypasses OAuth)
3. Calls functions directly (no HTTP overhead)
4. Shows formatted results in terminal

## Benefits

✅ **No Server Required** - Runs standalone  
✅ **No OAuth** - Bypasses authentication  
✅ **Instant Testing** - No HTTP latency  
✅ **Per-User State** - Maintains game state per session  
✅ **Full Functionality** - All 5 tools available  

## vs HTTP Client (`chess_client.py`)

| Feature | Local Tester | HTTP Client |
|---------|-------------|-------------|
| Server needed | ❌ No | ✅ Yes |
| OAuth required | ❌ No | ✅ Yes (or disable) |
| Speed | ⚡ Instant | 🐌 HTTP latency |
| Use case | Dev/testing | Integration testing |

## Troubleshooting

### "ModuleNotFoundError"

**Cause:** Can't find server modules

**Solution:** Make sure you're running from the project root:
```bash
cd /Users/jerel/Documents/Projects/ChessMCP
python3 chess_local_test.py
```

### "Authentication required"

This shouldn't happen with the mock user context. If it does, the context variable might not be set properly.

### Import Errors

If you see import errors, ensure all dependencies are installed:
```bash
cd server
pip3 install -r requirements.txt
```

## Development Workflow

Use this for rapid development:

1. Make changes to `server/main.py`
2. Test with `python3 chess_local_test.py`
3. Iterate quickly without restarting server
4. Once working, test with ChatGPT

## Note on Game State

Each time you run the local tester, it creates a **fresh game state** since it imports the modules new. Your game is isolated to that session.

For ChatGPT/HTTP server, game state persists per user across requests.

---

**Happy local testing!** ♟️🎮

