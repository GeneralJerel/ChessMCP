#!/usr/bin/env python3
"""
Test script for Chess MCP Server
Tests basic functionality without needing ChatGPT
"""

import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from server import chess_move, chess_reset
import server

def test_chess_move():
    """Test making chess moves"""
    print("=" * 50)
    print("Testing chess_move function")
    print("=" * 50)
    
    # Reset the game first
    print("\n1. Resetting game...")
    result = chess_reset()
    print(f"   Reset result: {result['content'][0]['text']}")
    assert result['structuredContent']['status'] == 'ongoing'
    print("   ✓ Game reset successfully")
    
    # Make first move - e4
    print("\n2. Making move: e4")
    result = chess_move("e4")
    print(f"   Result: {result['content'][0]['text']}")
    print(f"   FEN: {result['structuredContent']['fen']}")
    print(f"   Turn: {result['structuredContent']['turn']}")
    assert result['structuredContent']['turn'] == 'black'
    print("   ✓ Move e4 successful")
    
    # Make second move - e5
    print("\n3. Making move: e5")
    result = chess_move("e5")
    print(f"   Result: {result['content'][0]['text']}")
    print(f"   Turn: {result['structuredContent']['turn']}")
    assert result['structuredContent']['turn'] == 'white'
    print("   ✓ Move e5 successful")
    
    # Try invalid move
    print("\n4. Testing invalid move: e5 (already taken)")
    result = chess_move("e5")
    print(f"   Result: {result['content'][0]['text']}")
    assert 'error' in result['structuredContent']
    print("   ✓ Invalid move detected correctly")
    
    # Test knight move
    print("\n5. Making move: Nf3")
    result = chess_move("Nf3")
    print(f"   Result: {result['content'][0]['text']}")
    assert result['structuredContent']['turn'] == 'black'
    print("   ✓ Knight move successful")
    
    # Test move history
    print("\n6. Checking move history")
    print(f"   Moves made: {server.move_history}")
    assert len(server.move_history) == 3  # e4, e5, Nf3
    print("   ✓ Move history tracking works")
    
    print("\n" + "=" * 50)
    print("✓ All chess_move tests passed!")
    print("=" * 50)


def test_game_states():
    """Test different game states"""
    print("\n" + "=" * 50)
    print("Testing game state detection")
    print("=" * 50)
    
    # Reset and play fool's mate
    print("\n1. Setting up Fool's Mate scenario")
    chess_reset()
    
    moves = ["f3", "e6", "g4", "Qh4"]  # Fool's mate
    for i, move in enumerate(moves, 1):
        print(f"   Move {i}: {move}")
        result = chess_move(move)
        print(f"   Status: {result['structuredContent']['status']}")
    
    # Check if checkmate is detected
    assert result['structuredContent']['status'] == 'checkmate'
    print("\n   ✓ Checkmate detected correctly!")
    
    print("\n" + "=" * 50)
    print("✓ All game state tests passed!")
    print("=" * 50)


def test_resource():
    """Test HTML resource generation"""
    print("\n" + "=" * 50)
    print("Testing HTML widget resource")
    print("=" * 50)
    
    from server import get_chess_widget
    
    html = get_chess_widget()
    print(f"\n1. Widget HTML generated: {len(html)} characters")
    assert '<!DOCTYPE html>' in html
    assert 'chess-root' in html
    print("   ✓ HTML structure looks good")
    
    if 'chess.js' in html or 'console.error' in html:
        print("   ✓ JavaScript included or error message present")
    
    print("\n" + "=" * 50)
    print("✓ Resource generation test passed!")
    print("=" * 50)


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print(" Chess MCP Server - Test Suite")
    print("=" * 60)
    
    try:
        test_chess_move()
        test_game_states()
        test_resource()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Ensure Stockfish is installed (brew install stockfish)")
        print("2. Start the server: cd server && python3 server.py")
        print("3. Configure ChatGPT to use the MCP server")
        print("4. Try playing: 'ChessMCP e4'")
        print("\n")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

