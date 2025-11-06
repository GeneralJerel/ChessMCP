"""
Agent Service
Manages the ADK agent instance and provides helper functions
"""

import sys
import os
from pathlib import Path
from typing import Optional

# Add agent directory to path
AGENT_DIR = Path(__file__).parent.parent / "agent"
sys.path.insert(0, str(AGENT_DIR))

try:
    from agent import get_agent, chat_with_agent
except ImportError as e:
    print(f"Error importing agent module: {e}", file=sys.stderr)
    print(f"Make sure agent dependencies are installed: cd {AGENT_DIR} && pip install -r requirements.txt", file=sys.stderr)
    raise


# Singleton agent instance
_agent = None


def get_chess_agent():
    """Get or create the chess agent instance (singleton)"""
    global _agent
    if _agent is None:
        try:
            _agent = get_agent()
            print("Chess agent initialized successfully")
        except Exception as e:
            print(f"Error initializing chess agent: {e}", file=sys.stderr)
            raise
    return _agent


async def send_message_to_agent(message: str, session_id: Optional[str] = None) -> dict:
    """
    Send a message to the chess agent and get a response
    
    Args:
        message: User message
        session_id: Optional session ID for context
    
    Returns:
        dict with response, metadata, and success flag
    """
    try:
        result = await chat_with_agent(message, session_id)
        return result
    except Exception as e:
        return {
            "response": f"Agent error: {str(e)}",
            "metadata": {"error": str(e)},
            "success": False
        }


def initialize_agent():
    """Initialize the agent on startup"""
    try:
        get_chess_agent()
        return True
    except Exception as e:
        print(f"Failed to initialize agent: {e}", file=sys.stderr)
        return False

