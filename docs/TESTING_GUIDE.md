# Testing Guide for Chess Webapp

This guide walks you through testing the complete webapp implementation.

## Prerequisites for Testing

Before you can test, you need:

1. ✅ Python 3.8+ installed
2. ✅ Node.js 18+ installed  
3. ✅ Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))
4. ✅ All dependencies installed (see SETUP_GUIDE.md)

## Testing Phases

### Phase 1: Agent Testing (Isolated)

Test the ADK agent independently before integrating with the webapp.

```bash
cd agent

# Make sure .env file exists with GOOGLE_API_KEY
python3 agent.py
```

**Test Cases:**

1. **Basic Chat:**
   ```
   You: Hello, can you help me with chess?
   Expected: Friendly greeting and offer to help
   ```

2. **Make a Move:**
   ```
   You: Let's play chess! I'll start with e4
   Expected: Agent acknowledges move and makes a response
   ```

3. **Request Analysis:**
   ```
   You: What's the best move in this position?
   Expected: Agent uses chess_stockfish or suggests a move
   ```

4. **Check Game Status:**
   ```
   You: What's the current game status?
   Expected: Agent reports current position and turn
   ```

**Exit:** Press Ctrl+C

✅ If all test cases pass, the agent is working correctly.

---

### Phase 2: Backend API Testing

Test the backend API endpoints before connecting the frontend.

**Start the backend:**
```bash
cd webapp-backend
python3 main.py
```

You should see:
```
Starting Chess Webapp Backend on 0.0.0.0:8001
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Test Cases:**

1. **Health Check:**
   ```bash
   curl http://localhost:8001/health
   ```
   Expected: `{"status":"ok"}`

2. **Chat Health:**
   ```bash
   curl http://localhost:8001/api/chat/health
   ```
   Expected: `{"status":"ok","service":"chat"}`

3. **Send Chat Message:**
   ```bash
   curl -X POST http://localhost:8001/api/chat/message \
     -H "Content-Type: application/json" \
     -d '{"message":"Let'\''s play chess! e4","session_id":"test"}'
   ```
   Expected: JSON response with agent's reply

4. **API Documentation:**
   Open in browser: http://localhost:8001/docs
   Expected: Swagger UI with all endpoints

✅ If all endpoints respond correctly, the backend is working.

---

### Phase 3: Frontend Testing (Isolated)

Test the frontend UI before full integration.

**Start the frontend:**
```bash
cd webapp
npm run dev
```

You should see:
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

**Test Cases:**

1. **UI Loads:**
   - Open http://localhost:5173
   - Expected: Chess board displays, side panel visible

2. **Board Interaction:**
   - Try to drag a white pawn (e2)
   - Expected: Piece follows cursor

3. **Tabs Work:**
   - Click "Moves" tab
   - Click "Chat" tab
   - Expected: Tabs switch correctly

4. **Visual Design:**
   - Check if board has Lichess colors (brown and beige)
   - Check if layout is responsive
   - Expected: Professional, clean UI

✅ If the UI looks good and interactive elements work, frontend is ready.

---

### Phase 4: Full Integration Testing

Test the complete flow with all services running.

**Setup: Run both services**

Terminal 1:
```bash
cd webapp-backend
python3 main.py
```

Terminal 2:
```bash
cd webapp
npm run dev
```

**Test Case 1: Make Moves via Drag-Drop**

1. Open http://localhost:5173
2. Drag white pawn from e2 to e4
3. Check "Moves" tab
4. Expected: 
   - ✅ Move appears in history as "e4"
   - ✅ Pawn is now on e4
   - ✅ Board updates

**Test Case 2: Chat with Agent**

1. Click "Chat" tab
2. Type: "Hello! Can you help me learn chess?"
3. Click Send
4. Expected:
   - ✅ Your message appears in chat
   - ✅ Agent responds with helpful message
   - ✅ No errors in console

**Test Case 3: Agent Makes Moves**

1. In chat, type: "Let's start a new game. I'll play e4"
2. Wait for response
3. Expected:
   - ✅ Agent acknowledges the move
   - ✅ Board might update (depending on agent's response)

**Test Case 4: Request Analysis**

1. Make a few moves on the board
2. In chat, type: "What's the best move for white?"
3. Expected:
   - ✅ Agent analyzes position
   - ✅ Suggests a move with explanation

**Test Case 5: Ask for Stockfish Analysis**

1. In chat, type: "Analyze this position with Stockfish"
2. Expected:
   - ✅ Agent uses chess_stockfish tool
   - ✅ Returns best move and evaluation

**Test Case 6: Load a Puzzle**

1. In chat, type: "Show me a chess puzzle"
2. Expected:
   - ✅ Agent loads puzzle via chess_puzzle tool
   - ✅ Board might show puzzle position

**Test Case 7: Full Game**

1. Play a complete game by:
   - Making moves on the board
   - Asking agent for suggestions
   - Continuing until checkmate/draw
2. Expected:
   - ✅ All moves recorded in history
   - ✅ Game status updates correctly
   - ✅ Chat remains responsive

**Test Case 8: New Game**

1. Click "New Game" button
2. Expected:
   - ✅ Board resets to starting position
   - ✅ Move history clears
   - ✅ Chat history remains (as it should)

---

### Phase 5: Error Handling Testing

Test how the system handles errors.

**Test Case 1: Invalid Move**

1. Try to drag a piece to an illegal square
2. Expected:
   - ✅ Move is rejected
   - ✅ Piece returns to original position
   - ✅ No error message (silent rejection is fine)

**Test Case 2: Backend Offline**

1. Stop the backend (Ctrl+C in Terminal 1)
2. Try to send a chat message
3. Expected:
   - ✅ Error message displays in chat
   - ✅ Frontend doesn't crash

4. Restart backend
5. Try chat again
6. Expected:
   - ✅ Chat works again

**Test Case 3: Long Response**

1. Ask agent: "Explain the Sicilian Defense in detail"
2. Expected:
   - ✅ Loading indicator shows
   - ✅ Long response displays correctly
   - ✅ Chat auto-scrolls to bottom

---

### Phase 6: ChatGPT Widget Verification

Verify that the original ChatGPT widget still works.

**Important:** This ensures we haven't broken the existing integration.

1. Check git status:
   ```bash
   git diff server/main.py
   ```
   Expected: No changes (should be empty)

2. Test the widget in ChatGPT:
   - If you have the widget set up, try making a move
   - Expected: Widget works exactly as before

✅ If no changes to server/main.py and widget works, we're good!

---

### Phase 7: Performance Testing

Test system performance.

**Test Case 1: Multiple Rapid Moves**

1. Make 10 moves quickly on the board
2. Expected:
   - ✅ All moves register
   - ✅ No lag or freezing
   - ✅ Move history updates correctly

**Test Case 2: Multiple Chat Messages**

1. Send 5 messages quickly in chat
2. Expected:
   - ✅ All messages send
   - ✅ Responses come back in order
   - ✅ No messages lost

**Test Case 3: Long Session**

1. Keep the app open for 10+ minutes
2. Make moves periodically
3. Expected:
   - ✅ No memory leaks
   - ✅ Performance stays consistent

---

## Common Issues and Fixes

### Issue: "google-adk not installed"

```bash
cd agent
pip install -r requirements.txt
```

### Issue: "GOOGLE_API_KEY not set"

```bash
cd agent
# Create .env file
echo "GOOGLE_API_KEY=your_key_here" > .env
```

### Issue: Backend won't start

```bash
# Check if dependencies are installed
cd agent && pip install -r requirements.txt
cd ../webapp-backend && pip install -r requirements.txt

# Check if port 8001 is available
lsof -i :8001
```

### Issue: Frontend shows connection error

```bash
# Make sure backend is running
curl http://localhost:8001/health

# Check proxy config in webapp/vite.config.ts
```

### Issue: Agent doesn't respond

1. Check agent/.env has valid GOOGLE_API_KEY
2. Test agent directly: `cd agent && python3 agent.py`
3. Check backend logs for errors

### Issue: Moves don't update

1. Check browser console (F12) for errors
2. Verify chess.js is working correctly
3. Try refreshing the page

---

## Testing Checklist

Use this checklist to verify all functionality:

### Agent
- [ ] Agent CLI works independently
- [ ] Can make chess moves
- [ ] Can analyze positions
- [ ] Stockfish integration works

### Backend
- [ ] Health endpoints respond
- [ ] Chat endpoint accepts messages
- [ ] Agent integration works
- [ ] API docs accessible

### Frontend
- [ ] UI loads correctly
- [ ] Chess board renders
- [ ] Pieces can be dragged
- [ ] Tabs switch properly
- [ ] Chat interface works

### Integration
- [ ] Drag-drop makes moves
- [ ] Moves appear in history
- [ ] Chat sends to agent
- [ ] Agent responds in chat
- [ ] Agent can make moves
- [ ] Stockfish analysis works
- [ ] Puzzles load
- [ ] New game resets board

### Error Handling
- [ ] Invalid moves rejected
- [ ] Backend errors handled
- [ ] Frontend errors displayed

### Verification
- [ ] server/main.py unchanged
- [ ] ChatGPT widget works (if set up)

### Performance
- [ ] Rapid moves work
- [ ] No lag or freezing
- [ ] Long sessions stable

---

## Success Criteria

The implementation is successful if:

✅ All test cases pass
✅ No critical errors occur
✅ User experience is smooth
✅ ChatGPT widget unaffected
✅ Performance is acceptable

---

## After Testing

Once testing is complete:

1. **Document Issues:** Note any bugs or improvements needed
2. **Commit Changes:** Git commit with descriptive message
3. **Merge Branch:** Merge feature/webapp-ui into main (if ready)
4. **Deploy:** Follow production deployment guide

---

## Getting Help

If you encounter issues during testing:

1. Check console logs (browser F12 and terminal)
2. Review [WEBAPP_README.md](WEBAPP_README.md)
3. Check [SETUP_GUIDE.md](SETUP_GUIDE.md)
4. Look at individual service README files
5. Verify environment variables are set

---

**Happy Testing! 🎮♟️**

