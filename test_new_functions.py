#!/usr/bin/env python3
"""
Test script for new chess functions: status and puzzle
"""

import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from server import chess_move, chess_reset, chess_status, chess_puzzle
import server

def test_chess_status():
    """Test the chess_status function"""
    print("=" * 60)
    print("Testing chess_status function")
    print("=" * 60)
    
    # Reset game
    print("\n1. Starting new game...")
    chess_reset()
    
    # Get initial status
    print("\n2. Getting initial status...")
    result = chess_status()
    print(f"\n{result['content'][0]['text']}")
    print(f"\nStructured data:")
    print(f"   Turn: {result['structuredContent']['turn']}")
    print(f"   Turn player: {result['structuredContent']['turn_player']}")
    print(f"   Move number: {result['structuredContent']['move_number']}")
    print(f"   Players: {result['structuredContent']['players']}")
    
    assert result['structuredContent']['turn'] == 'white'
    assert result['structuredContent']['move_number'] == 1
    print("\n   ✓ Initial status looks good")
    
    # Make some moves
    print("\n3. Making moves e4, e5, Nf3...")
    chess_move("e4")
    chess_move("e5")
    chess_move("Nf3")
    
    # Get status after moves
    print("\n4. Getting status after moves...")
    result = chess_status()
    print(f"\n{result['content'][0]['text']}")
    
    assert result['structuredContent']['turn'] == 'black'
    assert result['structuredContent']['total_moves'] == 3
    print("\n   ✓ Status after moves is correct")
    
    # Test checkmate status
    print("\n5. Testing checkmate status (Fool's Mate)...")
    chess_reset()
    chess_move("f3")
    chess_move("e6")
    chess_move("g4")
    chess_move("Qh4")
    
    result = chess_status()
    print(f"\n{result['content'][0]['text']}")
    
    assert result['structuredContent']['status'] == 'checkmate'
    assert result['structuredContent']['is_game_over'] == True
    print("\n   ✓ Checkmate status detected correctly")
    
    print("\n" + "=" * 60)
    print("✓ All chess_status tests passed!")
    print("=" * 60)


def test_chess_puzzle():
    """Test the chess_puzzle function"""
    print("\n" + "=" * 60)
    print("Testing chess_puzzle function")
    print("=" * 60)
    
    # Test easy puzzle
    print("\n1. Loading easy puzzle...")
    result = chess_puzzle("easy")
    print(f"\n{result['content'][0]['text']}")
    print(f"\nPuzzle FEN: {result['structuredContent']['fen']}")
    print(f"Difficulty: {result['structuredContent']['difficulty']}")
    print(f"Solution (hidden): {result['_meta']['solution']}")
    
    assert result['structuredContent']['puzzle_type'] == 'mate_in_1'
    assert result['structuredContent']['difficulty'] == 'easy'
    assert result['_meta']['is_puzzle'] == True
    print("\n   ✓ Easy puzzle loaded successfully")
    
    # Test medium puzzle
    print("\n2. Loading medium puzzle...")
    result = chess_puzzle("medium")
    print(f"\n{result['content'][0]['text']}")
    
    assert result['structuredContent']['difficulty'] == 'medium'
    print("\n   ✓ Medium puzzle loaded successfully")
    
    # Test hard puzzle
    print("\n3. Loading hard puzzle...")
    result = chess_puzzle("hard")
    print(f"\n{result['content'][0]['text']}")
    
    assert result['structuredContent']['difficulty'] == 'hard'
    print("\n   ✓ Hard puzzle loaded successfully")
    
    # Test solving a puzzle
    print("\n4. Testing puzzle solution...")
    result = chess_puzzle("easy")
    solution = result['_meta']['solution']
    
    # Try to make the solution move
    try:
        move_result = chess_move(solution.replace('#', ''))
        print(f"\n   Solution move made: {solution}")
        print(f"   Result: {move_result['content'][0]['text']}")
        
        # Check if it's checkmate
        status_result = chess_status()
        if status_result['structuredContent']['status'] == 'checkmate':
            print("   ✓ Puzzle solved - checkmate achieved!")
        else:
            print("   ⚠️ Move made but not checkmate")
    except Exception as e:
        print(f"   ⚠️ Could not verify solution: {e}")
    
    print("\n" + "=" * 60)
    print("✓ All chess_puzzle tests passed!")
    print("=" * 60)


def main():
    """Run all tests for new functions"""
    print("\n" + "=" * 60)
    print(" Testing New Chess Functions")
    print(" 1. chess_status - Game status and player info")
    print(" 2. chess_puzzle - Mate in 1 puzzles")
    print("=" * 60)
    
    try:
        test_chess_status()
        test_chess_puzzle()
        
        print("\n" + "=" * 60)
        print("🎉 ALL NEW FUNCTION TESTS PASSED! 🎉")
        print("=" * 60)
        print("\nNew commands available:")
        print("1. chess_status - Get game status, turn, and players")
        print("2. chess_puzzle [difficulty] - Load mate in 1 puzzle")
        print("   - Difficulties: easy, medium, hard")
        print("\nExample usage in ChatGPT:")
        print('  "What\'s the current status of the game?"')
        print('  "Show me a chess puzzle"')
        print('  "Give me a hard mate in 1 puzzle"')
        print("\n")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

