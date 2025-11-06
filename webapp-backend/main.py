#!/usr/bin/env python3
"""
Chess Webapp Backend
FastAPI server that provides API endpoints for the chess webapp
Integrates with the ADK agent for chess assistance
"""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routes
from routes import chat

# Create FastAPI app
app = FastAPI(
    title="Chess Webapp Backend",
    description="Backend API for chess webapp with ADK agent integration",
    version="1.0.0"
)

# CORS middleware for development (allows Vite dev server at :5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # Alternative port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Chess Webapp Backend",
        "version": "1.0.0",
        "status": "running"
    }

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}

# Serve webapp static files in production
# Uncomment when ready to deploy
WEBAPP_DIST = Path(__file__).parent.parent / "webapp" / "dist"
if WEBAPP_DIST.exists():
    @app.get("/app/{full_path:path}")
    async def serve_webapp(full_path: str):
        """Serve webapp static files"""
        file_path = WEBAPP_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        # Fall back to index.html for SPA routing
        return FileResponse(WEBAPP_DIST / "index.html")
    
    # Serve webapp at root in production
    # app.mount("/", StaticFiles(directory=str(WEBAPP_DIST), html=True), name="webapp")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting Chess Webapp Backend on {host}:{port}")
    print(f"API docs available at: http://{host}:{port}/docs")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

