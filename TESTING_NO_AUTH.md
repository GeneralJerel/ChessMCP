# Testing Chess MCP - No Auth & Drag-and-Drop

## Prerequisites

1. Server is running on port 8000
2. ngrok or similar tunnel is exposing the server to the internet
3. Chess MCP is configured in ChatGPT

## Test Scenarios

### Test 1: Basic Move via Chat

1. Open ChatGPT
2. Start a conversation with Chess MCP enabled
3. Type: "Let's play chess. I'll play e4"
4. Verify:
   - ✅ ChatGPT calls `chess_move` tool
   - ✅ Board widget appears showing the move
   - ✅ No authentication required
   - ✅ ChatGPT suggests a response move

### Test 2: Drag-and-Drop Move

1. In the chess widget, drag a piece (e.g., knight from g1 to f3)
2. Verify:
   - ✅ Move validation occurs locally
   - ✅ "Nf3" appears in chat as your message
   - ✅ ChatGPT responds to the move
   - ✅ Board updates with new position

### Test 3: Stateless Game State

1. Make several moves: "e4", "e5", "Nf3", "Nc6"
2. Type: "What's the current position?"
3. Verify:
   - ✅ ChatGPT calls `chess_status` with current FEN
   - ✅ Status reflects all moves made
   - ✅ Game state is maintained across multiple turns

### Test 4: Game Reset

1. After playing some moves, type: "Reset the game"
2. Verify:
   - ✅ ChatGPT calls `chess_reset` tool
   - ✅ Board returns to starting position
   - ✅ New game can be started immediately

### Test 5: Puzzle Mode

1. Type: "Show me a chess puzzle"
2. Verify:
   - ✅ ChatGPT calls `chess_puzzle` tool
   - ✅ Board shows puzzle position
   - ✅ Puzzle FEN is different from starting position
   - ✅ Can make moves to solve puzzle

### Test 6: Stockfish Analysis

1. During a game, click "Ask Stockfish" button in the widget
2. Or type: "Analyze the position"
3. Verify:
   - ✅ ChatGPT calls `chess_stockfish` tool with current FEN
   - ✅ Analysis result is displayed
   - ✅ Best move suggestion is shown

### Test 7: Illegal Move Handling

1. Try to drag a piece to an illegal square
2. Verify:
   - ✅ Widget prevents illegal move locally
   - ✅ Piece returns to original position
   - ✅ No chat message is sent

### Test 8: Multiple Conversations

1. Start a new conversation
2. Play a different game
3. Verify:
   - ✅ New game starts fresh (no state from previous conversation)
   - ✅ Both conversations maintain their own game state
   - ✅ FEN in each conversation is independent

## Expected Behavior

### Move Flow
```
User drags piece (e2 to e4)
  ↓
Widget validates locally
  ↓
Widget sends "e4" to chat
  ↓
ChatGPT calls chess_move("e4", current_fen)
  ↓
Server returns new FEN
  ↓
Widget displays updated position
```

### FEN in Conversation
- Starting position: `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1`
- After e4: `rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1`
- ChatGPT automatically includes current FEN when calling tools

## Common Issues

### Issue: "Authentication required" error
**Solution:** 
- Check that `AuthenticationMiddleware` is removed
- Verify `securitySchemes: [{"type": "noauth"}]` is in tool definitions
- Restart the server

### Issue: Drag-and-drop doesn't work
**Solution:**
- Check that widget was rebuilt (`npm run build`)
- Verify `arePiecesDraggable={true}` in Chessboard component
- Check browser console for errors

### Issue: Game state not maintained
**Solution:**
- Verify FEN is being returned in tool responses
- Check that ChatGPT is including FEN when calling tools
- Ensure `structuredContent.fen` is present in responses

### Issue: Move appears in chat but board doesn't update
**Solution:**
- Check that `window.openai.sendFollowUpMessage` is called
- Verify widget is listening for toolOutput changes
- Check that FEN in response is valid

## Server Logs to Monitor

When testing, watch for these log entries:

```
[MCP] CallToolRequest: chess_move with args: {'move': 'e4', 'fen': '...'}
[MCP] CallToolRequest: chess_status with args: {'fen': '...'}
[MCP] CallToolRequest: chess_reset with args: {}
```

## Success Criteria

All of the following should work without authentication:
- ✅ Start a new game
- ✅ Make moves via chat
- ✅ Make moves via drag-and-drop
- ✅ Get game status
- ✅ Reset game
- ✅ Load puzzles
- ✅ Get Stockfish analysis
- ✅ Game state persists across conversation turns
- ✅ Multiple independent games in different conversations

