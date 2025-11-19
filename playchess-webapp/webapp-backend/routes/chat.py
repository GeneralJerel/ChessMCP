"""
Chat endpoints for communicating with the ADK agent
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path to import agent_service
sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_service import send_message_to_agent

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    metadata: dict
    success: bool


@router.post("/message", response_model=ChatResponse)
async def send_message(req: ChatRequest):
    """
    Send a message to the chess agent
    
    Args:
        req: Chat request with message and session_id
    
    Returns:
        Chat response with agent's reply
    """
    try:
        result = await send_message_to_agent(req.message, req.session_id)
        
        return ChatResponse(
            response=result.get("response", "No response"),
            metadata=result.get("metadata", {}),
            success=result.get("success", False)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with agent: {str(e)}"
        )


@router.get("/health")
async def chat_health():
    """Health check for chat service"""
    return {
        "status": "ok",
        "service": "chat"
    }


@router.post("/reset")
async def reset_conversation(session_id: Optional[str] = "default"):
    """
    Reset a conversation session
    
    Args:
        session_id: Session to reset
    
    Returns:
        Success message
    """
    # TODO: Implement session management
    return {
        "success": True,
        "message": f"Session {session_id} reset"
    }

