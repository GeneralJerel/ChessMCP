# Chess Webapp Setup Guide

Step-by-step guide to get the chess webapp running.

## Prerequisites

- Python 3.8+ (for backend and agent)
- Node.js 18+ (for frontend)
- Google Gemini API key

## Step 1: Get a Gemini API Key

1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API key"
3. Copy your API key
4. Keep it safe - you'll need it in Step 3

## Step 2: Install Dependencies

### Backend Dependencies

```bash
# Install agent dependencies
cd agent
pip install -r requirements.txt

# Install webapp-backend dependencies
cd ../webapp-backend
pip install -r requirements.txt
```

### Frontend Dependencies

```bash
cd ../webapp
npm install
```

## Step 3: Configure Environment

Create the agent `.env` file:

```bash
cd ../agent
cp env.template .env
```

Edit `agent/.env` and add your Gemini API key:
```
GOOGLE_API_KEY=your_actual_api_key_here
```

## Step 4: Test the Agent (Optional but Recommended)

```bash
cd agent
python3 agent.py
```

Try typing:
```
You: Let's play chess! I'll start with e4
```

If you see a response, the agent is working! Press Ctrl+C to exit.

## Step 5: Start the Services

You'll need **two terminal windows**.

### Terminal 1: Backend

```bash
cd webapp-backend
python3 main.py
```

You should see:
```
Starting Chess Webapp Backend on 0.0.0.0:8001
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Terminal 2: Frontend

```bash
cd webapp
npm run dev
```

You should see:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
```

## Step 6: Open the Webapp

Open your browser and go to: http://localhost:5173

You should see the chess board and side panel!

## Step 7: Test It Out

1. Try dragging a piece (e.g., pawn from e2 to e4)
2. Click the "Chat" tab
3. Type: "What's the best move for black?"
4. The AI assistant should respond!

## Troubleshooting

### Issue: "google-adk not installed"

```bash
cd agent
pip install google-adk
```

### Issue: "GOOGLE_API_KEY not set"

Make sure you created `agent/.env` with your API key:
```bash
cd agent
cat .env
# Should show: GOOGLE_API_KEY=your_key
```

### Issue: Frontend can't connect to backend

Check if backend is running:
```bash
curl http://localhost:8001/health
# Should return: {"status":"ok"}
```

### Issue: Port 8001 already in use

Change the port in `webapp-backend/main.py`:
```python
port = int(os.getenv("PORT", 8002))  # Change to 8002
```

And update `webapp/vite.config.ts`:
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8002',  // Change to 8002
```

### Issue: Backend crashes with Python errors

Make sure all dependencies are installed:
```bash
cd agent && pip install -r requirements.txt
cd ../webapp-backend && pip install -r requirements.txt
```

### Issue: npm install fails

Try deleting `node_modules` and `package-lock.json`:
```bash
cd webapp
rm -rf node_modules package-lock.json
npm install
```

## What's Next?

Once everything is running:

1. **Play some chess!** Drag pieces on the board
2. **Chat with the AI** - Ask it for help, analysis, or puzzles
3. **Check the moves tab** - See your game history

## Advanced

### Running in Production

See [WEBAPP_README.md](WEBAPP_README.md) for production deployment instructions.

### Testing the ChatGPT Widget

The existing ChatGPT widget still works! The webapp doesn't affect it at all.

### Customizing

- Change colors in `webapp/tailwind.config.js`
- Modify agent instructions in `agent/agent.py`
- Add new API endpoints in `webapp-backend/routes/`

## Getting Help

If you encounter issues:

1. Check the console logs in both terminals
2. Look for error messages in the browser console (F12)
3. Refer to [WEBAPP_README.md](WEBAPP_README.md) for detailed docs
4. Check individual README files in each directory

## Quick Reference

**Start Backend:**
```bash
cd webapp-backend && python3 main.py
```

**Start Frontend:**
```bash
cd webapp && npm run dev
```

**Test Agent:**
```bash
cd agent && python3 agent.py
```

**API Docs:**
http://localhost:8001/docs

**Webapp:**
http://localhost:5173

