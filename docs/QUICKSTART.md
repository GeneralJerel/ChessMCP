# Chess MCP - Quick Start Guide

## ✅ Installation Complete!

All components have been set up successfully:
- ✅ Python MCP server with chess logic
- ✅ React chess board widget
- ✅ MCP configuration in `~/.cursor/mcp.json`
- ✅ All tests passed

## 🚀 How to Use

### 1. Start Playing in ChatGPT

Simply type a chess move in your conversation:

```
ChessMCP e4
```

Or more naturally:

```
Let's play chess! I'll open with e4
```

The interactive chess board will appear showing your move!

### 2. Make Moves

Continue playing by typing moves in standard algebraic notation:

```
e4        # Pawn to e4
Nf3       # Knight to f3
exd5      # Pawn captures on d5
O-O       # Castle kingside
e8=Q      # Promote pawn to queen
```

### 3. Play Against ChatGPT

ChatGPT can act as your opponent. After you make a move, it will analyze the position and respond with its own move:

```
You: e4
ChatGPT: I'll play e5 [makes the move]
You: Nf3
ChatGPT: I'll develop my knight with Nc6 [makes the move]
```

### 4. Get Engine Analysis (Optional)

If you install Stockfish, you can click the "Ask Stockfish" button in the widget or ask:

```
What's the best move according to Stockfish?
```

**To install Stockfish:**
```bash
brew install stockfish
```

### 5. Start New Game

To reset and start a new game:

```
chess_reset
```

Or ask naturally:

```
Let's start a new game
```

## 📋 Example Game Session

```
You: Let's play chess! I'll start with e4

[Interactive board appears showing e4]

ChatGPT: Great! I'll respond with e5. This is one of the most popular 
         openings, leading to open games.

[Board updates showing e4 e5]

You: Nf3

[Board updates]

ChatGPT: I'll develop my knight with Nc6, defending the e5 pawn.

You: What does Stockfish recommend here?

ChatGPT: [Calls Stockfish analysis]
         Stockfish recommends: Bb5 (Ruy Lopez) with evaluation +0.35

You: Let's go with Bc4 instead

[Game continues...]
```

## 🎮 Move Notation Guide

| Notation | Meaning |
|----------|---------|
| e4 | Pawn to e4 |
| Nf3 | Knight to f3 |
| Bb5 | Bishop to b5 |
| Qh5 | Queen to h5 |
| exd5 | Pawn on e-file captures on d5 |
| Nxf7 | Knight captures on f7 |
| O-O | Castle kingside |
| O-O-O | Castle queenside |
| e8=Q | Promote pawn to queen |
| Qf7+ | Queen to f7, check |
| Qf7# | Queen to f7, checkmate |

## 🔧 Troubleshooting

### Widget Not Showing

If the board doesn't appear, make sure Cursor/ChatGPT has loaded the MCP server. You may need to restart Cursor.

### "Invalid Move" Error

- Check your notation (use uppercase for pieces: `Nf3` not `nf3`)
- Pawn moves use lowercase: `e4` not `E4`
- Make sure the move is legal in the current position

### Stockfish Not Working

Install Stockfish with:
```bash
brew install stockfish
```

If installed in a different location, update the path in `server/server.py`:
```python
STOCKFISH_PATH = "/path/to/your/stockfish"
```

## 🎯 What You Can Do

- ✅ Play full chess games with move validation
- ✅ View move history
- ✅ See check, checkmate, and stalemate detection
- ✅ Get AI opponent suggestions from ChatGPT
- ✅ Analyze positions with Stockfish engine
- ✅ Interactive visual board
- ✅ Support for all chess rules (castling, en passant, promotion)

## 📚 Advanced Usage

### Playing Multiple Games

Currently, the server maintains one game at a time. To start a new game, use `chess_reset`.

### Reviewing Positions

You can see the move history in the widget sidebar, showing the full game sequence.

### Engine Depth

Request deeper analysis:
```
Analyze this position with Stockfish at depth 20
```

### Opening Theory

Ask ChatGPT about openings:
```
What opening is this? [after several moves]
What are the main ideas in this position?
```

## 🎉 Enjoy Playing Chess!

Have fun playing chess through ChatGPT! The AI can:
- Explain moves and strategy
- Suggest improvements
- Teach opening theory
- Analyze endgames
- Calculate tactics
- And much more!

Happy playing! ♟️

