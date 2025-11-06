#!/usr/bin/env python3
"""
Chess ADK Agent
Connects to the Chess MCP server via stdio to provide chess assistance
"""

import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import ADK components
try:
    from google.adk import Agent
    from google.adk.mcp import StdioMCPClient
except ImportError:
    print("Error: google-adk not installed. Run: pip install google-adk", file=sys.stderr)
    sys.exit(1)

# Path to MCP server
MCP_SERVER_PATH = Path(__file__).parent.parent / "server" / "main.py"

# Check if Gemini API key is set
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GOOGLE_API_KEY or GEMINI_API_KEY not set in environment", file=sys.stderr)


class ChessAgentManager:
    """Manages the Chess ADK agent instance"""
    
    def __init__(self):
        self._agent: Optional[Agent] = None
        self._mcp_client: Optional[StdioMCPClient] = None
    
    def initialize(self) -> Agent:
        """Initialize and return the chess agent"""
        if self._agent is not None:
            return self._agent
        
        # Create MCP client that spawns the Chess MCP server
        self._mcp_client = StdioMCPClient(
            command="python3",
            args=[str(MCP_SERVER_PATH)],
            cwd=str(MCP_SERVER_PATH.parent)
        )
        
        # Create ADK agent with chess tools from MCP
        self._agent = Agent(
            name="chess_assistant",
            model="gemini-2.0-flash-exp",  # Use latest Gemini model
            instruction="""You are a helpful and knowledgeable chess assistant.

Your capabilities:
- Help users play chess by making moves using algebraic notation
- Analyze chess positions using Stockfish engine
- Provide strategic advice and explain chess concepts
- Load and solve chess puzzles
- Check game status and move history

When a user asks to make a move, use the chess_move tool with the move in algebraic notation.
When analyzing positions, use chess_stockfish to get engine recommendations.
Always explain your reasoning in a friendly and educational way.
If the user makes an illegal move, explain why and suggest legal alternatives.

Be encouraging and help players improve their chess skills!""",
            tools=self._mcp_client.get_tools()
        )
        
        return self._agent
    
    def get_agent(self) -> Agent:
        """Get the initialized agent (lazy initialization)"""
        if self._agent is None:
            return self.initialize()
        return self._agent
    
    async def chat(self, message: str, session_id: Optional[str] = None) -> dict:
        """
        Send a message to the agent and get a response
        
        Args:
            message: User message
            session_id: Optional session ID for maintaining conversation context
        
        Returns:
            dict with response and metadata
        """
        agent = self.get_agent()
        
        try:
            # Run the agent with the user's message
            response = await agent.run(message)
            
            return {
                "response": response.text if hasattr(response, 'text') else str(response),
                "metadata": response.metadata if hasattr(response, 'metadata') else {},
                "success": True
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "metadata": {"error": str(e)},
                "success": False
            }


# Global agent manager instance
_agent_manager = ChessAgentManager()


def get_agent() -> Agent:
    """Get the configured chess agent (singleton pattern)"""
    return _agent_manager.get_agent()


async def chat_with_agent(message: str, session_id: Optional[str] = None) -> dict:
    """
    Send a message to the chess agent
    
    Args:
        message: User message
        session_id: Optional session ID
    
    Returns:
        dict with response and metadata
    """
    return await _agent_manager.chat(message, session_id)


if __name__ == "__main__":
    # CLI interface for testing
    import asyncio
    
    async def main():
        print("Chess ADK Agent - Interactive Mode")
        print("=" * 50)
        print("Type your chess moves or questions. Type 'quit' to exit.")
        print()
        
        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Send to agent
                result = await chat_with_agent(user_input)
                
                if result["success"]:
                    print(f"Agent: {result['response']}")
                else:
                    print(f"Error: {result['response']}")
                print()
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    asyncio.run(main())

