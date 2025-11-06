#!/usr/bin/env python3
"""
Simple Local Chess Tester
Imports and tests chess functions directly without HTTP/OAuth
"""

import sys
sys.path.insert(0, '/Users/jerel/Documents/Projects/ChessMCP/server')

# Temporarily disable OAuth for local testing
import os
os.environ['GOOGLE_CLIENT_ID'] = 'test'
os.environ['GOOGLE_CLIENT_SECRET'] = 'test'
os.environ['MCP_SERVER_URL'] = 'http://localhost:8000'

# Import chess functions
from main import chess_move, chess_status, chess_reset, chess_puzzle, chess_stockfish

# Mock user context for local testing
from auth_middleware import UserContext, current_user_ctx

# Set a test user in the context
test_user = UserContext(
    email="local_test@example.com",
    user_id="test_user_123",
    name="Local Test User"
)
current_user_ctx.set(test_user)
print("✅ Set up test user context for local testing")


def print_help():
    """Print help menu"""
    print("""
♟️  Chess MCP Local Tester - Available Commands:

  move <notation>     Make a move (e.g., move e4, move Nf3)
  status              Show game status
  reset               Reset the game
  puzzle [difficulty] Load a puzzle (easy/medium/hard)
  stockfish [depth]   Get Stockfish analysis
  help                Show this help
  quit                Exit

Examples:
  move e4
  move Nf3
  status
  puzzle medium
  stockfish 20
""")


def format_result(result: dict):
    """Format and print tool result"""
    if "content" in result:
        for item in result["content"]:
            if item.get("type") == "text":
                print(f"✅ {item.get('text')}")
    
    if "structuredContent" in result:
        sc = result["structuredContent"]
        if "fen" in sc:
            print(f"   FEN: {sc['fen']}")
        if "turn" in sc:
            print(f"   Turn: {sc['turn']}")
        if "status" in sc:
            print(f"   Status: {sc['status']}")


def main():
    """Main interactive loop"""
    print("\n" + "="*60)
    print("♟️  Chess MCP Local Tester")
    print("="*60)
    print("Type 'help' for commands, 'quit' to exit")
    print("="*60)
    
    # Show initial status
    print("\n📊 Initial game status...")
    try:
        result = chess_status()
        format_result(result)
    except Exception as e:
        print(f"❌ Error: {e}")
    
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
                    print(f"\n♟️  Making move: {move}")
                    try:
                        result = chess_move(move)
                        format_result(result)
                    except Exception as e:
                        print(f"❌ Error: {e}")
            
            elif cmd == "status":
                print("\n📊 Game status...")
                try:
                    result = chess_status()
                    format_result(result)
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            elif cmd == "reset":
                print("\n🔄 Resetting game...")
                try:
                    result = chess_reset()
                    format_result(result)
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            elif cmd == "puzzle":
                difficulty = args[0] if args else "easy"
                if difficulty not in ["easy", "medium", "hard"]:
                    print(f"❌ Invalid difficulty. Use: easy, medium, or hard")
                else:
                    print(f"\n🧩 Loading {difficulty} puzzle...")
                    try:
                        result = chess_puzzle(difficulty)
                        format_result(result)
                    except Exception as e:
                        print(f"❌ Error: {e}")
            
            elif cmd == "stockfish":
                depth = int(args[0]) if args else 15
                print(f"\n🤖 Stockfish analysis (depth {depth})...")
                try:
                    result = chess_stockfish(depth)
                    format_result(result)
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            else:
                print(f"❌ Unknown command: {cmd}")
                print("   Type 'help' for available commands")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("♟️  Loading Chess MCP server modules...")
    main()

