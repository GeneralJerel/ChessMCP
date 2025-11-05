# How to Test Chess MCP with ChatGPT (Development Mode)

This guide shows you how to test your Chess MCP app in ChatGPT using ngrok to expose your local development server.

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ Chess MCP app built and ready (`npm run build` completed)
- ✅ Python server dependencies installed
- ✅ ngrok installed on your system
- ✅ ChatGPT account with developer mode access

---

## 🚀 Step-by-Step Setup

### Step 1: Build Your Chess App

Make sure your component is built:

```bash
cd /Users/jerel/Documents/Projects/ChessMCP
npm run build
```

Verify the build output:
```bash
ls -lh assets/chess-board.html
# Should show: chess-board.html (~331KB)
```

---

### Step 2: Start Your Local Server

Open a terminal and start the Python MCP server:

```bash
cd /Users/jerel/Documents/Projects/ChessMCP/server
python3 main.py
```

You should see:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

✅ **Server is running on port 8000**

> **Keep this terminal open!** The server needs to stay running.

---

### Step 3: Install ngrok (One-time Setup)

If you haven't installed ngrok yet:

**macOS:**
```bash
brew install ngrok
```

**Linux:**
```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list \
  && sudo apt update \
  && sudo apt install ngrok
```

**Windows:**
Download from https://ngrok.com/download

**Verify installation:**
```bash
ngrok version
```

---

### Step 4: Authenticate ngrok (One-time Setup)

1. Sign up at https://dashboard.ngrok.com/signup
2. Get your auth token from https://dashboard.ngrok.com/get-started/your-authtoken
3. Configure ngrok:

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

---

### Step 5: Expose Your Server with ngrok

Open a **new terminal window** (keep the server running in the first one):

```bash
ngrok http 8000
```

You'll see output like:

```
ngrok                                                                     

Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Latency                       35ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123xyz.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**📋 Copy the HTTPS Forwarding URL** (e.g., `https://abc123xyz.ngrok-free.app`)

> **Important Notes:**
> - This URL is temporary and changes each time you restart ngrok
> - Free ngrok URLs expire after 2 hours of inactivity
> - For permanent URLs, consider ngrok's paid plans

✅ **ngrok tunnel is active**

> **Keep this terminal open too!** The tunnel needs to stay active.

---

### Step 6: Enable ChatGPT Developer Mode

1. Go to https://chatgpt.com
2. Click on your profile (bottom left)
3. Select **Settings**
4. Look for **Beta Features** or **Developer Mode**
5. Enable **Developer Mode**

![ChatGPT Settings](https://platform.openai.com/docs/images/developer-mode.png)

> Note: Developer mode availability may vary by account type.

---

### Step 7: Add Your MCP Server to ChatGPT

1. In ChatGPT Settings, navigate to **Connectors** or **Actions**
2. Click **"Add Connector"** or **"+ New Action"**
3. Fill in the details:

   **Connector Name:**
   ```
   Chess MCP
   ```

   **Server URL:**
   ```
   https://YOUR-NGROK-URL.ngrok-free.app/mcp
   ```
   
   Replace `YOUR-NGROK-URL` with your actual ngrok subdomain (e.g., `abc123xyz`)

   **Description (optional):**
   ```
   Chess game with interactive board, move validation, and Stockfish analysis
   ```

4. Click **Save** or **Add**

✅ **Connector configured!**

---

### Step 8: Test in ChatGPT

Now you can test your Chess MCP app!

#### Option A: Add to Conversation Context

1. Start a **new conversation** in ChatGPT
2. Click the **"+"** or **"More"** button (usually near the message input)
3. Select **"Chess MCP"** from the list of connectors
4. The connector is now active in this conversation!

![Add Connector](https://github.com/user-attachments/assets/26852b36-7f9e-4f48-a515-aebd87173399)

#### Option B: Direct Invocation

Simply start chatting and mention chess-related actions:

**Try these commands:**

```
Let's play chess! I'll start with e4
```

```
chess_move e4
```

```
Show me the game status
```

```
Give me a chess puzzle
```

```
Ask Stockfish for the best move
```

The interactive chess board should appear in the conversation! ♟️

---

## 🎯 Quick Reference Card

| Terminal | Command | Purpose |
|----------|---------|---------|
| **Terminal 1** | `cd server && python3 main.py` | Run MCP server |
| **Terminal 2** | `ngrok http 8000` | Expose to internet |

| Component | URL | Purpose |
|-----------|-----|---------|
| **Local Server** | `http://localhost:8000` | MCP server |
| **ngrok Web UI** | `http://127.0.0.1:4040` | Monitor requests |
| **ChatGPT URL** | `https://YOUR.ngrok-free.app/mcp` | Connector endpoint |

---

## 🔍 Troubleshooting

### Problem: "Invalid Host Header" Error

**Solution:** Your server already has CORS configured. If you still see this, restart the server.

### Problem: Widget Doesn't Load

**Checklist:**
1. ✅ Component built? Run `npm run build`
2. ✅ File exists? Check `ls assets/chess-board.html`
3. ✅ Server restarted? Restart `python3 main.py` to pick up new assets

### Problem: ChatGPT Can't Reach Server

**Check ngrok status:**
```bash
# Verify ngrok is forwarding
curl https://YOUR-NGROK-URL.ngrok-free.app/mcp
```

**Check server logs:**
Look in Terminal 1 for incoming requests.

**Verify endpoint in ChatGPT:**
Make sure you added `/mcp` to the end of the URL.

### Problem: ngrok URL Changed

This is normal! Free ngrok URLs change on restart.

**Solutions:**
1. **Update ChatGPT connector** with the new URL (edit existing connector)
2. **Use ngrok reserved domain** (requires paid plan)
3. **Use ngrok config file** with fixed subdomain

### Problem: Connection Timeout

**Possible causes:**
- Firewall blocking ngrok
- Server crashed (check Terminal 1)
- ngrok session expired (free tier: 2 hours)

**Solutions:**
- Restart ngrok
- Restart the server
- Check firewall settings

---

## 🛠️ Advanced: ngrok Configuration File

For easier management, create `~/.ngrok/ngrok.yml`:

```yaml
version: 2
authtoken: YOUR_AUTH_TOKEN_HERE

tunnels:
  chess-mcp:
    proto: http
    addr: 8000
    # Uncomment for paid plan:
    # hostname: my-chess-app.ngrok.io
    
  chess-mcp-web:
    proto: http
    addr: 4444  # For assets if serving separately
```

Then start with:
```bash
ngrok start chess-mcp
```

---

## 📊 Monitoring Requests

ngrok provides a **web interface** at http://127.0.0.1:4040

Features:
- 🔍 **View all HTTP requests** in real-time
- 📝 **Inspect request/response** headers and bodies
- 🔄 **Replay requests** for debugging
- ⏱️ **See timing** information
- 📈 **Monitor traffic** patterns

Very useful for debugging ChatGPT ↔ Server communication!

---

## 🧪 Testing Commands

Once connected, try these in ChatGPT:

### Basic Moves
```
ChessMCP e4
Nf3
Let's play chess, I'll start with e4
```

### Game Status
```
chess_status
What's the current status of the game?
Who's turn is it?
```

### Puzzles
```
Show me a chess puzzle
Give me an easy puzzle
Load a hard mate in 1 puzzle
```

### Analysis
```
What's the best move according to Stockfish?
Analyze this position
chess_stockfish
```

### Reset
```
chess_reset
Let's start a new game
```

---

## 🎮 Expected Behavior

When everything is working correctly:

1. **You type a chess command** in ChatGPT
2. **ChatGPT calls your MCP server** via ngrok
3. **Your server processes the move** and validates it
4. **Server returns the widget HTML** with game state
5. **Interactive chess board appears** in the chat
6. **You can see the move** on the board
7. **Move history updates** automatically
8. **Game status displays** correctly

---

## 🔒 Security Considerations

### For Development

- ✅ ngrok provides HTTPS encryption
- ✅ CORS is properly configured
- ✅ No sensitive data in requests
- ⚠️ ngrok URLs are publicly accessible (but obscure)

### For Production

When deploying for real use:

1. **Deploy to a proper server** (not ngrok)
2. **Use environment-specific URLs**
3. **Add authentication** if needed
4. **Set up rate limiting**
5. **Use production CORS settings**
6. **Monitor and log requests**

---

## 💡 Pro Tips

### Tip 1: Keep URLs Consistent

Create a bash script `start-dev.sh`:

```bash
#!/bin/bash
# Terminal multiplexer to run both server and ngrok

# Start server in background
cd server
python3 main.py &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Start ngrok
ngrok http 8000

# Cleanup on exit
kill $SERVER_PID
```

### Tip 2: Quick Restart

If you need to rebuild and restart:

```bash
npm run build && cd server && python3 main.py
```

### Tip 3: Watch Mode

For rapid development, use Vite's dev mode:

```bash
# Terminal 1
npm run dev  # Vite with hot reload

# Terminal 2
cd server && python3 main.py  # Will auto-reload with uvicorn

# Terminal 3
ngrok http 8000
```

### Tip 4: Check Asset Serving

Test that your assets are accessible:

```bash
curl -I https://YOUR-NGROK-URL.ngrok-free.app/mcp
```

Should return HTTP 200 or appropriate MCP response.

---

## 📚 Additional Resources

- [OpenAI Apps SDK Documentation](https://developers.openai.com/apps-sdk)
- [ngrok Documentation](https://ngrok.com/docs)
- [Model Context Protocol Spec](https://spec.modelcontextprotocol.io/)
- [Apps SDK Examples](https://github.com/openai/openai-apps-sdk-examples)

---

## 🎉 Success Checklist

Before considering your setup complete, verify:

- [ ] Component builds without errors (`npm run build`)
- [ ] Server starts on port 8000
- [ ] ngrok tunnel is active and forwarding
- [ ] ngrok URL is copied correctly
- [ ] ChatGPT connector is added with `/mcp` endpoint
- [ ] Connector appears in ChatGPT "More" menu
- [ ] Chess command triggers the board widget
- [ ] Moves are validated correctly
- [ ] Board updates in real-time
- [ ] All 5 tools work (move, status, puzzle, stockfish, reset)

---

## 🆘 Getting Help

If you're still having issues:

1. **Check server logs** in Terminal 1
2. **Check ngrok logs** in Terminal 2 and web UI (http://127.0.0.1:4040)
3. **Check browser console** in ChatGPT (F12 → Console)
4. **Verify all steps** above were completed
5. **Try a simple curl test** to the ngrok URL

---

## 🎯 What's Next?

Once testing works:

- ✅ Play full games with ChatGPT as opponent
- ✅ Solve tactical puzzles
- ✅ Get engine analysis
- ✅ Test all game scenarios (checkmate, stalemate, etc.)
- ✅ Deploy to production (see deployment guides)

---

**Happy Testing! ♟️🎮**

*Last updated: November 6, 2025*

