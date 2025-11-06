#!/usr/bin/env python3
"""
Simple MCP Client for Chess
Connects to the Chess MCP server locally for testing
"""

import requests
import json
import sys
from typing import Dict, Any, Optional


class ChessMCPClient:
    """Simple MCP client for testing Chess server locally"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
        print(f"🔌 Connecting to Chess MCP Server at {base_url}")
        self._test_connection()
    
    def _test_connection(self):
        """Test server connectivity"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server is online")
            else:
                print(f"⚠️  Server responded with status {response.status_code}")
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            print("   Make sure the server is running: python3 server/main.py")
            sys.exit(1)
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Optional[Dict]:
        """
        Call an MCP tool on the server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
        
        Returns:
            Tool response or None if error
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/mcp",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", {})
            else:
                print(f"❌ Server returned status {response.status_code}: {response.text}")
                return None
        
        except Exception as e:
            print(f"❌ Error calling tool: {e}")
            return None
    
    def make_move(self, move: str) -> bool:
        """Make a chess move"""
        print(f"\n♟️  Making move: {move}")
        result = self.call_tool("chess_move", {"move": move})
        
        if result:
            content = result.get("content", [])
            if content and len(content) > 0:
                print(f"✅ {content[0].get('text', '')}")
                
                # Print structured content if available
                structured = result.get("structuredContent", {})
                if structured:
                    print(f"   FEN: {structured.get('fen', '')}")
                    print(f"   Turn: {structured.get('turn', '')}")
                    print(f"   Status: {structured.get('status', '')}")
                return True
            else:
                print(f"⚠️  Unexpected response: {result}")
        
        return False
    
    def get_status(self) -> bool:
        """Get game status"""
        print("\n📊 Getting game status...")
        result = self.call_tool("chess_status", {})
        
        if result:
            content = result.get("content", [])
            if content and len(content) > 0:
                print(content[0].get('text', ''))
                return True
        
        return False
    
    def reset_game(self) -> bool:
        """Reset the game"""
        print("\n🔄 Resetting game...")
        result = self.call_tool("chess_reset", {})
        
        if result:
            content = result.get("content", [])
            if content and len(content) > 0:
                print(f"✅ {content[0].get('text', '')}")
                return True
        
        return False
    
    def get_puzzle(self, difficulty: str = "easy") -> bool:
        """Load a chess puzzle"""
        print(f"\n🧩 Loading {difficulty} puzzle...")
        result = self.call_tool("chess_puzzle", {"difficulty": difficulty})
        
        if result:
            content = result.get("content", [])
            if content and len(content) > 0:
                print(content[0].get('text', ''))
                return True
        
        return False
    
    def get_stockfish_analysis(self, depth: int = 15) -> bool:
        """Get Stockfish analysis"""
        print(f"\n🤖 Getting Stockfish analysis (depth {depth})...")
        result = self.call_tool("chess_stockfish", {"depth": depth})
        
        if result:
            content = result.get("content", [])
            if content and len(content) > 0:
                print(f"✅ {content[0].get('text', '')}")
                return True
        
        return False
    
    def list_tools(self) -> bool:
        """List available tools"""
        print("\n📋 Available tools:")
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/mcp",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                tools = result.get("result", {}).get("tools", [])
                for i, tool in enumerate(tools, 1):
                    print(f"  {i}. {tool.get('name')} - {tool.get('description')}")
                return True
            else:
                print(f"❌ Error listing tools: {response.status_code}")
                return False
        
        except Exception as e:
            print(f"❌ Error listing tools: {e}")
            return False


def print_help():
    """Print help menu"""
    print("""
♟️  Chess MCP Client - Available Commands:

  move <notation>     Make a move (e.g., move e4, move Nf3)
  status              Show game status
  reset               Reset the game
  puzzle [difficulty] Load a puzzle (easy/medium/hard)
  stockfish [depth]   Get Stockfish analysis
  tools               List available tools
  help                Show this help
  quit                Exit the client

Examples:
  move e4
  move Nf3
  status
  puzzle medium
  stockfish 20
""")


def interactive_mode(client: ChessMCPClient):
    """Interactive CLI mode"""
    print("\n" + "="*60)
    print("♟️  Chess MCP Client - Interactive Mode")
    print("="*60)
    print("Type 'help' for commands, 'quit' to exit")
    print("="*60)
    
    # Show initial status
    client.get_status()
    
    while True:
        try:
            command = input("\n♟️  > ").strip()
            
            if not command:
                continue
            
            parts = command.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            if cmd == "quit" or cmd == "exit":
                print("\n👋 Goodbye! Thanks for playing!")
                break
            
            elif cmd == "help":
                print_help()
            
            elif cmd == "move":
                if not args:
                    print("❌ Usage: move <notation> (e.g., move e4)")
                else:
                    move = args[0]
                    client.make_move(move)
            
            elif cmd == "status":
                client.get_status()
            
            elif cmd == "reset":
                client.reset_game()
            
            elif cmd == "puzzle":
                difficulty = args[0] if args else "easy"
                if difficulty not in ["easy", "medium", "hard"]:
                    print(f"❌ Invalid difficulty. Use: easy, medium, or hard")
                else:
                    client.get_puzzle(difficulty)
            
            elif cmd == "stockfish":
                depth = int(args[0]) if args else 15
                client.get_stockfish_analysis(depth)
            
            elif cmd == "tools":
                client.list_tools()
            
            else:
                print(f"❌ Unknown command: {cmd}")
                print("   Type 'help' for available commands")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main entry point"""
    # Check if server URL provided
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    # Create client
    client = ChessMCPClient(server_url)
    
    # Run interactive mode
    interactive_mode(client)


if __name__ == "__main__":
    main()

