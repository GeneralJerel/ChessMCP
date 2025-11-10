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
from main import chess_move, chess_multimove, chess_status, chess_reset, chess_puzzle, chess_check_puzzle_solution, chess_stockfish

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
  multimove <moves>   Make multiple moves (e.g., multimove e4 c5, multimove 1. e4 c5 2. Nf3)
  status              Show game status
  reset               Reset the game
  puzzle [id]         Load a puzzle (optionally specify ID 1-25000)
  check <move>        Check if a move solves the current puzzle
  stockfish [depth]   Get Stockfish analysis
  help                Show this help
  quit                Exit

Examples:
  move e4
  multimove e4 c5
  multimove 1. e4 c5 2. Nf3 d6
  status
  puzzle
  puzzle 42
  check Qg7
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
    
    # Track current puzzle state
    current_puzzle_id = None
    current_puzzle_fen = None
    
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
            
            elif cmd == "multimove":
                if not args:
                    print("❌ Usage: multimove <moves> (e.g., multimove e4 c5, multimove 1. e4 c5 2. Nf3)")
                else:
                    moves = " ".join(args)
                    print(f"\n♟️  Making moves: {moves}")
                    try:
                        result = chess_multimove(moves)
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
                puzzle_id_arg = int(args[0]) if args else None
                print(f"\n🧩 Loading puzzle{f' #{puzzle_id_arg}' if puzzle_id_arg else ''}...")
                try:
                    result = chess_puzzle(puzzle_id_arg)
                    format_result(result)
                    # Store puzzle state for check command
                    if "structuredContent" in result:
                        sc = result["structuredContent"]
                        current_puzzle_id = sc.get("puzzle_id")
                        current_puzzle_fen = sc.get("fen")
                        if current_puzzle_id:
                            print(f"\n💡 Use 'check <move>' to submit your solution")
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            elif cmd == "check":
                if not args:
                    print("❌ Usage: check <move> (e.g., check Qg7)")
                elif current_puzzle_id is None or current_puzzle_fen is None:
                    print("❌ No puzzle loaded. Use 'puzzle' to load one first.")
                else:
                    move = args[0]
                    print(f"\n🔍 Checking move: {move}")
                    try:
                        result = chess_check_puzzle_solution(move, current_puzzle_id, current_puzzle_fen)
                        format_result(result)
                        # If incorrect, puzzle state remains the same
                        # If correct, clear puzzle state
                        if "structuredContent" in result and result["structuredContent"].get("correct"):
                            current_puzzle_id = None
                            current_puzzle_fen = None
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

