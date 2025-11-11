#!/usr/bin/env python3
"""
Chess MCP Server
Provides chess game functionality via Model Context Protocol
Following OpenAI Apps SDK best practices
With Google OAuth 2.1 authentication
"""

import chess
import chess.pgn
import requests
import json
from typing import Optional, Dict, List, Any
from pathlib import Path
from functools import lru_cache
from mcp.server.fastmcp import FastMCP
import mcp.types as types
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

# OAuth imports (kept for OAuth endpoints, but not used for MCP auth)
from oauth_config import oauth_config
from auth_middleware import AuthenticationMiddleware, get_current_user
from client_store import client_store
from auth_code_store import auth_code_store
from jwt_keys import jwt_key_manager
from oauth_proxy import authorization_endpoint, oauth_callback, token_endpoint, jwks_endpoint

# Initialize FastMCP
mcp = FastMCP("chess-mcp", stateless_http=True)

# Assets directory
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

# MIME type for HTML widgets
MIME_TYPE = "text/html+skybridge"

# Path to stockfish binary (update this path if needed)
STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"  # Common macOS path


def get_game_status(board: chess.Board) -> str:
    """Get current game status"""
    if board.is_checkmate():
        return "checkmate"
    elif board.is_stalemate():
        return "stalemate"
    elif board.is_insufficient_material():
        return "draw_insufficient_material"
    elif board.is_check():
        return "check"
    else:
        return "ongoing"


def format_move_history(move_history: List[str]) -> str:
    """Format move history in algebraic notation"""
    if not move_history:
        return "No moves yet"
    
    formatted = []
    for i in range(0, len(move_history), 2):
        move_num = (i // 2) + 1
        white_move = move_history[i]
        black_move = move_history[i + 1] if i + 1 < len(move_history) else ""
        if black_move:
            formatted.append(f"{move_num}. {white_move} {black_move}")
        else:
            formatted.append(f"{move_num}. {white_move}")
    
    return " ".join(formatted)


@mcp.tool(
    name="chess_multimove",
    title="Make multiple chess moves",
    description="Make multiple moves on the chess board at once using algebraic notation. Supports formats like 'e4 c5', '1. e4 c5', or '1. e4 c5 2. Nf3 d6'",
    annotations={
        "readOnlyHint": False,
        "openai/outputTemplate": "ui://widget/chess-board.html",
        "openai/toolInvocation/invoking": "Making moves...",
        "openai/toolInvocation/invoked": "Moves played"
    }
)
def chess_multimove(moves: str, fen: str = None) -> dict:
    """
    Make multiple chess moves on the board at once.
    
    Args:
        moves: Multiple moves in algebraic notation (e.g., "e4 c5", "1. e4 c5", "1. e4 c5 2. Nf3 d6")
        fen: Optional FEN string representing current position. If not provided, uses starting position.
    
    Returns:
        Dictionary containing the updated game state after all moves
    """
    # Create board from FEN or use starting position
    try:
        if fen:
            current_game = chess.Board(fen)
        else:
            current_game = chess.Board()
    except ValueError as e:
        return {
            "content": [{"type": "text", "text": f"Invalid FEN: {str(e)}"}],
            "structuredContent": {"error": "invalid_fen"}
        }
    
    # Parse moves - handle various formats like "e4 c5", "1. e4 c5", "1. e4 c5 2. Nf3"
    import re
    # Remove move numbers (e.g., "1.", "2.")
    moves_cleaned = re.sub(r'\d+\.', '', moves)
    # Split by whitespace
    move_list = moves_cleaned.split()
    
    if not move_list:
        return {
            "content": [{"type": "text", "text": "No moves provided"}],
            "structuredContent": {"error": "no_moves"}
        }
    
    played_moves = []
    
    try:
        # Apply each move sequentially
        for move in move_list:
            if not move.strip():
                continue
            
            chess_move_obj = current_game.parse_san(move)
            current_game.push(chess_move_obj)
            played_moves.append(move)
        
        # Get game status
        status = get_game_status(current_game)
        
        # Get legal moves for next turn
        legal_moves = [current_game.san(m) for m in current_game.legal_moves]
        
        # Prepare response
        response = {
            "success": True,
            "moves": played_moves,
            "moves_count": len(played_moves),
            "fen": current_game.fen(),
            "turn": "white" if current_game.turn == chess.WHITE else "black",
            "status": status,
            "legal_moves_count": len(legal_moves),
            "is_check": current_game.is_check(),
            "is_checkmate": current_game.is_checkmate(),
            "is_stalemate": current_game.is_stalemate()
        }
        
        # Format message
        moves_played_text = ", ".join(played_moves)
        if status == "checkmate":
            winner = "Black" if current_game.turn == chess.WHITE else "White"
            message = f"Checkmate! {winner} wins. Moves played: {moves_played_text}"
        elif status == "stalemate":
            message = f"Stalemate! The game is a draw. Moves played: {moves_played_text}"
        elif status == "check":
            message = f"Check! Moves played: {moves_played_text}"
        else:
            message = f"{len(played_moves)} moves played: {moves_played_text}"
        
        return {
            "content": [{"type": "text", "text": message}],
            "structuredContent": {
                "fen": response["fen"],
                "moves": played_moves,
                "status": status,
                "turn": response["turn"]
            },
            "_meta": {
                "full_state": response,
                "legal_moves": legal_moves[:50]  # Limit for metadata
            }
        }
        
    except ValueError as e:
        return {
            "content": [{"type": "text", "text": f"Invalid move sequence. Error at move '{move}': {str(e)}. Successfully played: {', '.join(played_moves) if played_moves else 'none'}"}],
            "structuredContent": {
                "error": str(e),
                "fen": current_game.fen(),
                "played_moves": played_moves
            }
        }


@mcp.tool(
    name="chess_move",
    title="Make a chess move",
    description="Make a move on the chess board using algebraic notation",
    annotations={
        "readOnlyHint": False,
        "openai/outputTemplate": "ui://widget/chess-board.html",
        "openai/toolInvocation/invoking": "Making move...",
        "openai/toolInvocation/invoked": "Move played"
    }
)
def chess_move(move: str, fen: str = None) -> dict:
    """
    Make a chess move on the board.
    
    Args:
        move: The move in algebraic notation (e.g., "e4", "Nf3", "O-O", "e8=Q")
        fen: Optional FEN string representing current position. If not provided, uses starting position.
    
    Returns:
        Dictionary containing the updated game state
    """
    # Create board from FEN or use starting position
    try:
        if fen:
            current_game = chess.Board(fen)
        else:
            current_game = chess.Board()
    except ValueError as e:
        return {
            "content": [{"type": "text", "text": f"Invalid FEN: {str(e)}"}],
            "structuredContent": {"error": "invalid_fen"}
        }
    
    # Build move history from the board
    move_history = []
    
    try:
        # Try to parse and make the move
        chess_move_obj = current_game.parse_san(move)
        current_game.push(chess_move_obj)
        
        # Get game status
        status = get_game_status(current_game)
        
        # Get legal moves for next turn
        legal_moves = [current_game.san(m) for m in current_game.legal_moves]
        
        # Prepare response
        response = {
            "success": True,
            "move": move,
            "fen": current_game.fen(),
            "turn": "white" if current_game.turn == chess.WHITE else "black",
            "status": status,
            "legal_moves_count": len(legal_moves),
            "is_check": current_game.is_check(),
            "is_checkmate": current_game.is_checkmate(),
            "is_stalemate": current_game.is_stalemate()
        }
        
        # Format message for ChatGPT
        if status == "checkmate":
            winner = "Black" if current_game.turn == chess.WHITE else "White"
            message = f"Checkmate! {winner} wins. Move played: {move}"
        elif status == "stalemate":
            message = f"Stalemate! The game is a draw. Move played: {move}"
        elif status == "check":
            message = f"Check! Move played: {move}"
        else:
            message = f"Move played: {move}"
        
        return {
            "content": [{"type": "text", "text": message}],
            "structuredContent": {
                "fen": response["fen"],
                "move": move,
                "status": status,
                "turn": response["turn"]
            },
            "_meta": {
                "full_state": response,
                "legal_moves": legal_moves[:50]  # Limit for metadata
            }
        }
        
    except ValueError as e:
        return {
            "content": [{"type": "text", "text": f"Invalid move: {move}. Error: {str(e)}"}],
            "structuredContent": {
                "error": str(e),
                "fen": current_game.fen()
            }
        }


@mcp.tool(
    name="chess_stockfish",
    title="Analyze with Stockfish",
    description="Get engine analysis of the current position",
    annotations={
        "readOnlyHint": True,
        "openai/widgetAccessible": True,
        "openai/toolInvocation/invoking": "Analyzing position...",
        "openai/toolInvocation/invoked": "Analysis complete"
    }
)
def chess_stockfish(depth: int = 10, fen: str = None) -> dict:
    """
    Analyze the current position using Stockfish engine.
    
    Args:
        depth: Analysis depth (default: 15)
        fen: Optional FEN string representing current position. If not provided, uses starting position.
    
    Returns:
        Dictionary containing engine analysis and best move
    """
    # Create board from FEN or use starting position
    try:
        if fen:
            current_game = chess.Board(fen)
        else:
            current_game = chess.Board()
    except ValueError as e:
        return {
            "content": [{"type": "text", "text": f"Invalid FEN: {str(e)}"}],
            "structuredContent": {"error": "invalid_fen"}
        }
    
    try:
        import stockfish as sf
        
        # Check if Stockfish exists
        stockfish_path = STOCKFISH_PATH
        if not Path(stockfish_path).exists():
            # Try alternative paths
            alternatives = [
                "/usr/local/bin/stockfish",
                "/usr/bin/stockfish",
                "/opt/homebrew/Cellar/stockfish/16/bin/stockfish"
            ]
            for alt in alternatives:
                if Path(alt).exists():
                    stockfish_path = alt
                    break
            else:
                return {
                    "content": [{"type": "text", "text": f"Stockfish not found. Please install it with: brew install stockfish"}],
                    "structuredContent": {"error": "Stockfish not found"}
                }
        
        # Initialize Stockfish
        engine = sf.Stockfish(path=stockfish_path)
        engine.set_depth(depth)
        engine.set_fen_position(current_game.fen())
        
        # Get best move
        best_move = engine.get_best_move()
        evaluation = engine.get_evaluation()
        
        # Convert UCI move to SAN
        try:
            uci_move = chess.Move.from_uci(best_move)
            san_move = current_game.san(uci_move)
        except:
            san_move = best_move
        
        # Format evaluation
        if evaluation["type"] == "mate":
            eval_text = f"Mate in {evaluation['value']}"
        else:
            centipawns = evaluation["value"]
            eval_text = f"{centipawns / 100:.2f}"
            if centipawns > 0:
                eval_text = f"+{eval_text}"
        
        message = f"Stockfish recommends: {san_move} (Evaluation: {eval_text})"
        
        return {
            "content": [{"type": "text", "text": message}],
            "structuredContent": {
                "best_move": san_move,
                "best_move_uci": best_move,
                "evaluation": eval_text,
                "depth": depth
            },
            "_meta": {
                "fen": current_game.fen(),
                "raw_evaluation": evaluation
            }
        }
        
    except ImportError:
        return {
            "content": [{"type": "text", "text": "Stockfish library not available"}],
            "structuredContent": {"error": "Stockfish not installed"}
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error running Stockfish: {str(e)}"}],
            "structuredContent": {"error": str(e)}
        }


@mcp.tool(
    name="chess_play_move",
    title="Make a chess move against Stockfish",
    description="Make a chess move as White against Stockfish. Stockfish will automatically respond as Black. You are an engaging chess coach - provide tips, commentary, and playful taunts about both moves.",
    annotations={
        "readOnlyHint": False,
        "openai/outputTemplate": "ui://widget/chess-board.html",
        "openai/toolInvocation/invoking": "Playing your move and Stockfish is thinking...",
        "openai/toolInvocation/invoked": "Stockfish has responded!",
        "openai/widgetAccessible": True
    }
)
def chess_play_move(move: str, fen: str = None, depth: int = 10, move_history: str = None) -> dict:
    """
    Make a chess move as White against Stockfish engine.
    
    Args:
        move: User's move in algebraic notation (e.g., "e4", "Nf3")
        fen: Optional FEN string representing current position. If not provided, uses starting position.
        depth: Stockfish analysis depth (default: 10 for fast response)
        move_history: JSON string of previous moves in SAN notation
    
    Returns:
        Dictionary containing both moves (user's and Stockfish's) with game state and coaching hints
    """
    # Parse existing move history
    import json
    try:
        move_list = json.loads(move_history) if move_history else []
    except (json.JSONDecodeError, TypeError):
        move_list = []
    
    # Create board from FEN or use starting position
    try:
        if fen:
            current_game = chess.Board(fen)
        else:
            current_game = chess.Board()
    except ValueError as e:
        return {
            "content": [{"type": "text", "text": f"Invalid FEN: {str(e)}"}],
            "structuredContent": {"error": "invalid_fen"}
        }
    
    # Verify it's White's turn
    if current_game.turn != chess.WHITE:
        return {
            "content": [{"type": "text", "text": "It's not White's turn! Stockfish plays as Black."}],
            "structuredContent": {"error": "wrong_turn", "turn": "black"}
        }
    
    # Apply user's move
    try:
        user_move_obj = current_game.parse_san(move)
        current_game.push(user_move_obj)
        user_move_san = move
    except ValueError as e:
        # Get legal moves to help user
        legal_moves = [current_game.san(m) for m in current_game.legal_moves]
        return {
            "content": [{"type": "text", "text": f"Illegal move: {move}. Legal moves: {', '.join(legal_moves[:10])}"}],
            "structuredContent": {
                "error": "illegal_move",
                "attempted_move": move,
                "legal_moves": legal_moves[:50]
            }
        }
    
    # Check if game ended after user's move
    user_move_status = get_game_status(current_game)
    if user_move_status in ["checkmate", "stalemate", "draw_insufficient_material"]:
        message = f"You played {user_move_san}. "
        if user_move_status == "checkmate":
            message += "Checkmate! You win! 🎉"
        elif user_move_status == "stalemate":
            message += "Stalemate! It's a draw."
        else:
            message += "Draw by insufficient material."
        
        return {
            "content": [{"type": "text", "text": message}],
            "structuredContent": {
                "user_move": user_move_san,
                "stockfish_move": None,
                "fen": current_game.fen(),
                "status": user_move_status,
                "turn": "white" if current_game.turn == chess.WHITE else "black"
            }
        }
    
    # Get Stockfish's response
    try:
        import stockfish as sf
        
        # Check if Stockfish exists
        stockfish_path = STOCKFISH_PATH
        if not Path(stockfish_path).exists():
            # Try alternative paths
            alternatives = [
                "/usr/local/bin/stockfish",
                "/usr/bin/stockfish",
                "/opt/homebrew/Cellar/stockfish/16/bin/stockfish",
                "/opt/homebrew/Cellar/stockfish/17/bin/stockfish"
            ]
            for alt in alternatives:
                if Path(alt).exists():
                    stockfish_path = alt
                    break
            else:
                return {
                    "content": [{"type": "text", "text": f"You played {user_move_san}, but Stockfish is not available. Please install it with: brew install stockfish"}],
                    "structuredContent": {
                        "error": "Stockfish not found",
                        "user_move": user_move_san,
                        "fen": current_game.fen()
                    }
                }
        
        # Initialize Stockfish
        engine = sf.Stockfish(path=stockfish_path)
        engine.set_depth(depth)
        engine.set_fen_position(current_game.fen())
        
        # Get evaluation before Stockfish's move
        eval_before = engine.get_evaluation()
        
        # Get Stockfish's best move
        stockfish_move_uci = engine.get_best_move()
        
        if not stockfish_move_uci:
            # No legal moves for Black (should not happen, but handle it)
            return {
                "content": [{"type": "text", "text": f"You played {user_move_san}. Game over!"}],
                "structuredContent": {
                    "user_move": user_move_san,
                    "stockfish_move": None,
                    "fen": current_game.fen(),
                    "status": user_move_status,
                    "turn": "white" if current_game.turn == chess.WHITE else "black"
                }
            }
        
        # Convert UCI to SAN and apply Stockfish's move
        stockfish_move_obj = chess.Move.from_uci(stockfish_move_uci)
        stockfish_move_san = current_game.san(stockfish_move_obj)
        current_game.push(stockfish_move_obj)
        
        # Get final game status after Stockfish's move
        final_status = get_game_status(current_game)
        
        # Get evaluation after Stockfish's move
        engine.set_fen_position(current_game.fen())
        eval_after = engine.get_evaluation()
        
        # Format evaluation for display
        def format_eval(evaluation):
            if evaluation["type"] == "mate":
                mate_in = evaluation["value"]
                if mate_in > 0:
                    return f"Mate in {mate_in}"
                else:
                    return f"Mate in {abs(mate_in)}"
            else:
                centipawns = evaluation["value"]
                eval_text = f"{centipawns / 100:.2f}"
                if centipawns > 0:
                    eval_text = f"+{eval_text}"
                return eval_text
        
        eval_text = format_eval(eval_after)
        
        # Determine coaching hints based on position
        coaching_hints = {
            "evaluation": eval_text,
            "depth": depth
        }
        
        # Detect tactical themes
        if current_game.is_check():
            coaching_hints["tactical_themes"] = ["check"]
        
        # Detect evaluation swings
        if eval_before["type"] == "cp" and eval_after["type"] == "cp":
            eval_change = eval_after["value"] - eval_before["value"]
            coaching_hints["evaluation_change"] = eval_change / 100.0
            
            if abs(eval_change) > 200:  # Significant swing (2+ pawns)
                if eval_change < -200:
                    coaching_hints["position_note"] = "blunder_detected"
                elif eval_change > 200:
                    coaching_hints["position_note"] = "excellent_move"
        
        # Build response message
        message = f"You played {user_move_san}. Stockfish responded with {stockfish_move_san}. "
        
        if final_status == "checkmate":
            winner = "Black" if current_game.turn == chess.WHITE else "White"
            message += f"Checkmate! {winner} wins!"
        elif final_status == "check":
            message += "Check!"
        elif final_status == "stalemate":
            message += "Stalemate! It's a draw."
        else:
            message += f"Position evaluation: {eval_text}"
        
        # Get legal moves for next turn
        legal_moves = [current_game.san(m) for m in current_game.legal_moves]
        
        # Update move history with both moves
        move_list.append(user_move_san)
        move_list.append(stockfish_move_san)
        
        return {
            "content": [{"type": "text", "text": message}],
            "structuredContent": {
                "user_move": user_move_san,
                "stockfish_move": stockfish_move_san,
                "fen": current_game.fen(),
                "evaluation": eval_text,
                "status": final_status,
                "turn": "white" if current_game.turn == chess.WHITE else "black",
                "is_check": current_game.is_check(),
                "is_checkmate": current_game.is_checkmate(),
                "is_stalemate": current_game.is_stalemate()
            },
            "_meta": {
                "coaching_hints": coaching_hints,
                "legal_moves": legal_moves[:50],
                "move_history_list": move_list,
                "full_state": {
                    "user_move": user_move_san,
                    "stockfish_move": stockfish_move_san,
                    "stockfish_move_uci": stockfish_move_uci,
                    "legal_moves_count": len(legal_moves)
                }
            }
        }
        
    except ImportError:
        return {
            "content": [{"type": "text", "text": f"You played {user_move_san}, but Stockfish library is not available. Install with: pip install stockfish"}],
            "structuredContent": {
                "error": "Stockfish library not installed",
                "user_move": user_move_san,
                "fen": current_game.fen()
            }
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"You played {user_move_san}. Error getting Stockfish response: {str(e)}"}],
            "structuredContent": {
                "error": str(e),
                "user_move": user_move_san,
                "fen": current_game.fen()
            }
        }


@mcp.tool(
    name="chess_reset",
    title="Reset chess game",
    description="Reset the game to starting position. Start a fresh game vs Stockfish. Encourage the user and set an upbeat tone.",
    annotations={
        "readOnlyHint": False,
        "openai/outputTemplate": "ui://widget/chess-board.html",
        "openai/toolInvocation/invoking": "Resetting game...",
        "openai/toolInvocation/invoked": "Game reset"
    }
)
def chess_reset() -> dict:
    """
    Reset the chess game to the starting position.
    
    Returns:
        Dictionary confirming the reset with starting FEN
    """
    # Create a new board at starting position
    starting_board = chess.Board()
    
    return {
        "content": [{"type": "text", "text": "Chess game reset to starting position"}],
        "structuredContent": {
            "fen": starting_board.fen(),
            "status": "ongoing",
            "turn": "white"
        },
        "_meta": {
            "move_history_list": []
        }
    }


@mcp.tool(
    name="chess_status",
    title="Get game status",
    description="Get current game status, turn, and player information",
    annotations={
        "readOnlyHint": True,
        "openai/toolInvocation/invoking": "Getting status...",
        "openai/toolInvocation/invoked": "Status retrieved"
    }
)
def chess_status(fen: str = None) -> dict:
    """
    Get the current status of the chess game.
    
    Args:
        fen: Optional FEN string representing current position. If not provided, uses starting position.
    
    Returns:
        Dictionary containing game status, turn, players, and move count
    """
    # Create board from FEN or use starting position
    try:
        if fen:
            current_game = chess.Board(fen)
        else:
            current_game = chess.Board()
    except ValueError as e:
        return {
            "content": [{"type": "text", "text": f"Invalid FEN: {str(e)}"}],
            "structuredContent": {"error": "invalid_fen"}
        }
    
    # Default player names for stateless mode
    player_white = "White"
    player_black = "Black"
    
    # Get current turn
    turn_color = "White" if current_game.turn == chess.WHITE else "Black"
    turn_player = player_white if current_game.turn == chess.WHITE else player_black
    
    # Get game status
    status = get_game_status(current_game)
    
    # Count moves
    full_moves = current_game.fullmove_number
    
    # Build status message
    if status == "checkmate":
        winner = player_black if current_game.turn == chess.WHITE else player_white
        message = f"🏁 Game Over - Checkmate!\n"
        message += f"👑 Winner: {winner}\n"
        message += f"📊 Total moves: {full_moves - 1}"
    elif status == "stalemate":
        message = f"🏁 Game Over - Stalemate (Draw)\n"
        message += f"📊 Total moves: {full_moves}"
    elif status == "draw_insufficient_material":
        message = f"🏁 Game Over - Draw (Insufficient Material)\n"
        message += f"📊 Total moves: {full_moves}"
    elif status == "check":
        message = f"⚠️ Check!\n"
        message += f"🎯 {turn_player} ({turn_color}) to move\n"
        message += f"📊 Move {full_moves}"
    else:
        message = f"♟️ Game in Progress\n"
        message += f"🎯 {turn_player} ({turn_color}) to move\n"
        message += f"📊 Move {full_moves}"
    
    # Add players info
    message += f"\n\n👥 Players:\n"
    message += f"   White: {player_white}\n"
    message += f"   Black: {player_black}"
    
    return {
        "content": [{"type": "text", "text": message}],
        "structuredContent": {
            "status": status,
            "turn": turn_color.lower(),
            "turn_player": turn_player,
            "players": {
                "white": player_white,
                "black": player_black
            },
            "move_number": full_moves,
            "fen": current_game.fen(),
            "is_check": current_game.is_check(),
            "is_game_over": current_game.is_game_over()
        },
        "_meta": {
            "legal_moves_count": len(list(current_game.legal_moves))
        }
    }


@mcp.tool(
    name="chess_puzzle",
    title="Show mate in 1 puzzle",
    description="Load a mate-in-one puzzle position for the user to solve from a database of 25,000+ puzzles",
    annotations={
        "readOnlyHint": False,
        "openai/outputTemplate": "ui://widget/chess-board.html",
        "openai/toolInvocation/invoking": "Loading puzzle...",
        "openai/toolInvocation/invoked": "Puzzle loaded"
    }
)
def chess_puzzle(puzzle_id: int = None) -> dict:
    """
    Load a mate-in-one puzzle for the user to solve from the database.
    
    Args:
        puzzle_id: Optional specific puzzle ID (1-25000). If not provided, selects randomly.
    
    Returns:
        Dictionary with puzzle position and instructions
    """
    import random
    import csv
    
    # Load puzzles from CSV
    csv_path = Path(__file__).parent / "data" / "mate-in-one.csv"
    
    if not csv_path.exists():
        return {
            "content": [{"type": "text", "text": "❌ Puzzle database not found. Please ensure mate-in-one.csv exists in server/data/"}],
            "structuredContent": {"error": "puzzle_database_not_found"}
        }
    
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            puzzles = list(reader)
        
        # Select puzzle
        if puzzle_id is not None:
            # Use specific puzzle (1-indexed for user-friendliness)
            if puzzle_id < 1 or puzzle_id > len(puzzles):
                return {
                    "content": [{"type": "text", "text": f"❌ Invalid puzzle ID. Please use a number between 1 and {len(puzzles)}"}],
                    "structuredContent": {"error": "invalid_puzzle_id"}
                }
            puzzle = puzzles[puzzle_id - 1]
            actual_id = puzzle_id
        else:
            # Random puzzle
            actual_id = random.randint(1, len(puzzles))
            puzzle = puzzles[actual_id - 1]
        
        fen = puzzle['fen']
        solution_uci = puzzle['best']
        
        # Convert UCI to SAN for display
        board = chess.Board(fen)
        solution_move = chess.Move.from_uci(solution_uci)
        solution_san = board.san(solution_move)
        
        # Create message
        message = f"🧩 Mate in 1 Puzzle (#{actual_id})\n\n"
        message += f"White to move and checkmate in one move!\n\n"
        message += f"Find the winning move. Use chess_check_puzzle_solution to submit your answer."
        
        return {
            "content": [{"type": "text", "text": message}],
            "structuredContent": {
                "fen": fen,
                "puzzle_type": "mate_in_1",
                "puzzle_id": actual_id,
                "turn": "white",
                "status": "puzzle"
            },
            "_meta": {
                "solution_uci": solution_uci,
                "solution_san": solution_san,
                "puzzle_id": actual_id,
                "is_puzzle": True,
                "move_history_list": []
            }
        }
    
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"❌ Error loading puzzle: {str(e)}"}],
            "structuredContent": {"error": str(e)}
        }


@mcp.tool(
    name="chess_check_puzzle_solution",
    title="Check puzzle solution",
    description="Check if a move is the correct solution to the current puzzle",
    annotations={
        "readOnlyHint": False,
        "openai/outputTemplate": "ui://widget/chess-board.html",
        "openai/toolInvocation/invoking": "Checking solution...",
        "openai/toolInvocation/invoked": "Solution checked"
    }
)
def chess_check_puzzle_solution(move: str, puzzle_id: int, fen: str) -> dict:
    """
    Check if a move is the correct solution to a puzzle.
    
    Args:
        move: The move to check in algebraic notation (e.g., "Qg7", "Ra8")
        puzzle_id: The puzzle ID being solved
        fen: The puzzle's FEN position
    
    Returns:
        Dictionary indicating if the solution is correct, with the resulting position if correct
    """
    import csv
    
    # Load the specific puzzle
    csv_path = Path(__file__).parent / "data" / "mate-in-one.csv"
    
    if not csv_path.exists():
        return {
            "content": [{"type": "text", "text": "❌ Puzzle database not found."}],
            "structuredContent": {"error": "puzzle_database_not_found"}
        }
    
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            puzzles = list(reader)
        
        if puzzle_id < 1 or puzzle_id > len(puzzles):
            return {
                "content": [{"type": "text", "text": "❌ Invalid puzzle ID"}],
                "structuredContent": {"error": "invalid_puzzle_id"}
            }
        
        puzzle = puzzles[puzzle_id - 1]
        correct_fen = puzzle['fen']
        solution_uci = puzzle['best']
        
        # Verify FEN matches
        if fen.split()[0] != correct_fen.split()[0]:  # Compare just piece positions
            return {
                "content": [{"type": "text", "text": "❌ FEN mismatch. Please reload the puzzle."}],
                "structuredContent": {"error": "fen_mismatch"}
            }
        
        # Create board and check the move
        board = chess.Board(fen)
        
        try:
            # Parse the user's move
            user_move = board.parse_san(move)
            user_move_uci = user_move.uci()
            
            # Check if it matches the solution
            if user_move_uci == solution_uci:
                # Correct! Apply the move and show the mate
                board.push(user_move)
                
                # Verify it's checkmate
                if board.is_checkmate():
                    message = f"🎉 Correct! {move} is checkmate!\n\n"
                    message += f"Brilliant! You found the winning move.\n\n"
                    message += f"Would you like to try another puzzle? Use chess_puzzle to get a new one!"
                    
                    return {
                        "content": [{"type": "text", "text": message}],
                        "structuredContent": {
                            "fen": board.fen(),
                            "correct": True,
                            "status": "checkmate",
                            "turn": "black",
                            "puzzle_solved": True
                        },
                        "_meta": {
                            "puzzle_id": puzzle_id,
                            "solution": move
                        }
                    }
                else:
                    # This shouldn't happen with correct puzzle data
                    message = f"✅ That's the correct move ({move}), but let me verify...\n\n"
                    message += f"The position after your move is:\n{board.fen()}"
                    
                    return {
                        "content": [{"type": "text", "text": message}],
                        "structuredContent": {
                            "fen": board.fen(),
                            "correct": True,
                            "status": get_game_status(board),
                            "turn": "white" if board.turn == chess.WHITE else "black"
                        }
                    }
            else:
                # Incorrect move
                message = f"❌ Not quite! {move} is not the solution.\n\n"
                message += f"💡 Try again! Look for a move that delivers checkmate in one.\n\n"
                message += f"The puzzle is still set up - try a different move!"
                
                return {
                    "content": [{"type": "text", "text": message}],
                    "structuredContent": {
                        "fen": fen,  # Return original puzzle position
                        "correct": False,
                        "puzzle_id": puzzle_id,
                        "turn": "white",
                        "status": "puzzle"
                    },
                    "_meta": {
                        "puzzle_id": puzzle_id,
                        "attempted_move": move
                    }
                }
        
        except ValueError as e:
            # Invalid move notation
            message = f"❌ Invalid move: {move}\n\n"
            message += f"Error: {str(e)}\n\n"
            message += f"Please use standard algebraic notation (e.g., Qg7, Ra8, Nf3)"
            
            return {
                "content": [{"type": "text", "text": message}],
                "structuredContent": {
                    "fen": fen,
                    "error": "invalid_move",
                    "puzzle_id": puzzle_id
                }
            }
    
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"❌ Error checking solution: {str(e)}"}],
            "structuredContent": {"error": str(e)}
        }


# Widget HTML loading
@lru_cache(maxsize=None)
def load_widget_html(component_name: str) -> str:
    """Load widget HTML from assets directory"""
    html_path = ASSETS_DIR / f"{component_name}.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf8")
    
    raise FileNotFoundError(
        f'Widget HTML for "{component_name}" not found in {ASSETS_DIR}. '
        "Run `npm run build` to generate the assets before starting the server."
    )


def tool_meta(uri: str) -> Dict[str, Any]:
    """Generate tool metadata"""
    return {
        "openai/outputTemplate": uri,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
    }


# Register MCP protocol handlers

@mcp._mcp_server.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available MCP tools for ChatGPT discovery"""
    return [
        types.Tool(
            name="chess_multimove",
            title="Make multiple chess moves",
            description="Make multiple moves on the chess board at once using algebraic notation. Supports formats like 'e4 c5', '1. e4 c5', or '1. e4 c5 2. Nf3 d6'",
            inputSchema={
                "type": "object",
                "properties": {
                    "moves": {
                        "type": "string",
                        "description": "Multiple moves in standard algebraic notation (e.g., 'e4 c5', '1. e4 c5', '1. e4 c5 2. Nf3 d6')"
                    },
                    "fen": {
                        "type": "string",
                        "description": "Optional FEN string representing current position. If not provided, uses starting position."
                    }
                },
                "required": ["moves"],
                "additionalProperties": False
            },
            _meta={
                "openai/outputTemplate": "ui://widget/chess-board.html",
                "openai/widgetAccessible": True,
                "openai/resultCanProduceWidget": True,
                "openai/toolInvocation/invoking": "Making moves...",
                "openai/toolInvocation/invoked": "Moves played",
                "securitySchemes": [{"type": "noauth"}]
            },
            annotations={
                "readOnlyHint": False,
                "destructiveHint": False,
                "openWorldHint": False,
            }
        ),
        types.Tool(
            name="chess_move",
            title="Make a chess move",
            description="Make a move on the chess board using algebraic notation (e.g., e4, Nf3, O-O, e8=Q)",
            inputSchema={
                "type": "object",
                "properties": {
                    "move": {
                        "type": "string",
                        "description": "Move in standard algebraic notation"
                    },
                    "fen": {
                        "type": "string",
                        "description": "Optional FEN string representing current position. If not provided, uses starting position."
                    }
                },
                "required": ["move"],
                "additionalProperties": False
            },
            _meta={
                "openai/outputTemplate": "ui://widget/chess-board.html",
                "openai/widgetAccessible": True,
                "openai/resultCanProduceWidget": True,
                "openai/toolInvocation/invoking": "Making move...",
                "openai/toolInvocation/invoked": "Move played",
                "securitySchemes": [{"type": "noauth"}]
            },
            annotations={
                "readOnlyHint": False,
                "destructiveHint": False,
                "openWorldHint": False,
            }
        ),
        types.Tool(
            name="chess_play_move",
            title="Make a chess move against Stockfish",
            description="Make a chess move as White against Stockfish. Stockfish will automatically respond as Black. You are an engaging chess coach - provide tips, commentary, and playful taunts about both moves.",
            inputSchema={
                "type": "object",
                "properties": {
                    "move": {
                        "type": "string",
                        "description": "User's move in standard algebraic notation (e.g., e4, Nf3, O-O)"
                    },
                    "fen": {
                        "type": "string",
                        "description": "Optional FEN string representing current position. If not provided, uses starting position."
                    },
                    "depth": {
                        "type": "integer",
                        "description": "Stockfish analysis depth (default: 10 for fast response)",
                        "default": 10
                    }
                },
                "required": ["move"],
                "additionalProperties": False
            },
            _meta={
                "openai/outputTemplate": "ui://widget/chess-board.html",
                "openai/widgetAccessible": True,
                "openai/resultCanProduceWidget": True,
                "openai/toolInvocation/invoking": "Playing your move and Stockfish is thinking...",
                "openai/toolInvocation/invoked": "Stockfish has responded!",
                "securitySchemes": [{"type": "noauth"}]
            },
            annotations={
                "readOnlyHint": False,
                "destructiveHint": False,
                "openWorldHint": False,
            }
        ),
        types.Tool(
            name="chess_status",
            title="Get game status",
            description="Get current game status, turn, player information, and move count",
            inputSchema={
                "type": "object",
                "properties": {
                    "fen": {
                        "type": "string",
                        "description": "Optional FEN string representing current position. If not provided, uses starting position."
                    }
                },
                "additionalProperties": False
            },
            _meta={
                "openai/toolInvocation/invoking": "Getting status...",
                "openai/toolInvocation/invoked": "Status retrieved",
                "securitySchemes": [{"type": "noauth"}]
            },
            annotations={
                "readOnlyHint": True,
                "destructiveHint": False,
                "openWorldHint": False,
            }
        ),
        types.Tool(
            name="chess_reset",
            title="Reset chess game",
            description="Reset the chess game to the starting position",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            _meta={
                "openai/outputTemplate": "ui://widget/chess-board.html",
                "openai/widgetAccessible": True,
                "openai/resultCanProduceWidget": True,
                "openai/toolInvocation/invoking": "Resetting game...",
                "openai/toolInvocation/invoked": "Game reset",
                "securitySchemes": [{"type": "noauth"}]
            },
            annotations={
                "readOnlyHint": False,
                "destructiveHint": False,
                "openWorldHint": False,
            }
        ),
        types.Tool(
            name="chess_puzzle",
            title="Show mate in 1 puzzle",
            description="Load a mate-in-one puzzle position for the user to solve from a database of 25,000+ puzzles",
            inputSchema={
                "type": "object",
                "properties": {
                    "puzzle_id": {
                        "type": "integer",
                        "description": "Optional specific puzzle ID (1-25000). If not provided, selects randomly.",
                        "minimum": 1,
                        "maximum": 25000
                    }
                },
                "additionalProperties": False
            },
            _meta={
                "openai/outputTemplate": "ui://widget/chess-board.html",
                "openai/widgetAccessible": True,
                "openai/resultCanProduceWidget": True,
                "openai/toolInvocation/invoking": "Loading puzzle...",
                "openai/toolInvocation/invoked": "Puzzle loaded",
                "securitySchemes": [{"type": "noauth"}]
            },
            annotations={
                "readOnlyHint": False,
                "destructiveHint": False,
                "openWorldHint": False,
            }
        ),
        types.Tool(
            name="chess_check_puzzle_solution",
            title="Check puzzle solution",
            description="Check if a move is the correct solution to the current mate-in-1 puzzle. Returns the mated position if correct, or asks to try again if incorrect.",
            inputSchema={
                "type": "object",
                "properties": {
                    "move": {
                        "type": "string",
                        "description": "The move to check in standard algebraic notation (e.g., 'Qg7', 'Ra8', 'Nf3')"
                    },
                    "puzzle_id": {
                        "type": "integer",
                        "description": "The puzzle ID being solved (provided when puzzle was loaded)"
                    },
                    "fen": {
                        "type": "string",
                        "description": "The puzzle's FEN position (provided when puzzle was loaded)"
                    }
                },
                "required": ["move", "puzzle_id", "fen"],
                "additionalProperties": False
            },
            _meta={
                "openai/outputTemplate": "ui://widget/chess-board.html",
                "openai/widgetAccessible": True,
                "openai/resultCanProduceWidget": True,
                "openai/toolInvocation/invoking": "Checking solution...",
                "openai/toolInvocation/invoked": "Solution checked",
                "securitySchemes": [{"type": "noauth"}]
            },
            annotations={
                "readOnlyHint": False,
                "destructiveHint": False,
                "openWorldHint": False,
            }
        ),
        types.Tool(
            name="chess_stockfish",
            title="Analyze with Stockfish",
            description="Get Stockfish engine analysis of the current chess position",
            inputSchema={
                "type": "object",
                "properties": {
                    "depth": {
                        "type": "integer",
                        "description": "Analysis depth (default: 15, higher is more accurate but slower)",
                        "default": 15,
                        "minimum": 1,
                        "maximum": 30
                    },
                    "fen": {
                        "type": "string",
                        "description": "Optional FEN string representing current position. If not provided, uses starting position."
                    }
                },
                "additionalProperties": False
            },
            _meta={
                "openai/widgetAccessible": True,
                "openai/toolInvocation/invoking": "Analyzing position...",
                "openai/toolInvocation/invoked": "Analysis complete",
                "securitySchemes": [{"type": "noauth"}]
            },
            annotations={
                "readOnlyHint": True,
                "destructiveHint": False,
                "openWorldHint": False,
            }
        ),
    ]


@mcp._mcp_server.list_resources()
async def list_resources() -> List[types.Resource]:
    """List available HTML widget resources"""
    return [
        types.Resource(
            uri="ui://widget/chess-board.html",
            name="Chess Board Widget",
            title="Chess Board Widget",
            description="Interactive chess board showing the current game position with move history",
            mimeType=MIME_TYPE,
            _meta=tool_meta("ui://widget/chess-board.html"),
        )
    ]


@mcp._mcp_server.list_resource_templates()
async def list_resource_templates() -> List[types.ResourceTemplate]:
    """List available resource templates"""
    return [
        types.ResourceTemplate(
            name="Chess Board Widget",
            title="Chess Board Widget",
            uriTemplate="ui://widget/chess-board.html",
            description="Interactive chess board showing the current game position with move history",
            mimeType=MIME_TYPE,
            _meta=tool_meta("ui://widget/chess-board.html"),
        )
    ]


async def handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    """Handle resource read requests"""
    uri = str(req.params.uri)
    
    if uri == "ui://widget/chess-board.html":
        try:
            html = load_widget_html("chess-board")
            return types.ServerResult(
                types.ReadResourceResult(
                    contents=[
                        types.TextResourceContents(
                            uri=uri,
                            mimeType=MIME_TYPE,
                            text=html,
                            _meta=tool_meta(uri),
                        )
                    ]
                )
            )
        except FileNotFoundError as e:
            return types.ServerResult(
                types.ReadResourceResult(
                    contents=[],
                    _meta={"error": str(e)},
                )
            )
    
    return types.ServerResult(
        types.ReadResourceResult(
            contents=[],
            _meta={"error": f"Unknown resource: {uri}"},
        )
    )


async def handle_call_tool(req: types.CallToolRequest) -> types.ServerResult:
    """
    Handle tool call requests from ChatGPT.
    Routes to appropriate @mcp.tool() decorated functions.
    """
    tool_name = req.params.name
    arguments = req.params.arguments or {}
    
    print(f"[MCP] CallToolRequest: {tool_name} with args: {arguments}")
    
    try:
        # Route to the appropriate tool function
        if tool_name == "chess_multimove":
            result = chess_multimove(
                arguments.get("moves", ""),
                arguments.get("fen")
            )
        elif tool_name == "chess_move":
            result = chess_move(
                arguments.get("move", ""),
                arguments.get("fen")
            )
        elif tool_name == "chess_play_move":
            result = chess_play_move(
                arguments.get("move", ""),
                arguments.get("fen"),
                arguments.get("depth", 10),
                arguments.get("move_history")
            )
        elif tool_name == "chess_status":
            result = chess_status(arguments.get("fen"))
        elif tool_name == "chess_reset":
            result = chess_reset()
        elif tool_name == "chess_puzzle":
            result = chess_puzzle(arguments.get("puzzle_id"))
        elif tool_name == "chess_check_puzzle_solution":
            result = chess_check_puzzle_solution(
                arguments.get("move", ""),
                arguments.get("puzzle_id", 0),
                arguments.get("fen", "")
            )
        elif tool_name == "chess_stockfish":
            result = chess_stockfish(
                arguments.get("depth", 15),
                arguments.get("fen")
            )
        else:
            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Unknown tool: {tool_name}"
                        )
                    ],
                    isError=True
                )
            )
        
        # Convert tool result to MCP CallToolResult
        content = []
        for item in result.get("content", []):
            if item.get("type") == "text":
                content.append(
                    types.TextContent(
                        type="text",
                        text=item.get("text", "")
                    )
                )
        
        return types.ServerResult(
            types.CallToolResult(
                content=content,
                structuredContent=result.get("structuredContent", {}),
                _meta=result.get("_meta", {})
            )
        )
    
    except Exception as e:
        print(f"[MCP] Error calling tool {tool_name}: {e}")
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Error executing {tool_name}: {str(e)}"
                    )
                ],
                isError=True
            )
        )


# Register the request handlers
mcp._mcp_server.request_handlers[types.CallToolRequest] = handle_call_tool
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = handle_read_resource


# Create ASGI app
app = mcp.streamable_http_app()


# ===== OAuth 2.1 Endpoints (using Starlette routing) =====

from starlette.routing import Route, Mount
from starlette.responses import Response as StarletteResponse

async def protected_resource_metadata(request: Request):
    """
    RFC 9728: OAuth 2.0 Protected Resource Metadata
    Returns metadata about this MCP server as a protected resource.
    """
    print(f"[OAuth] Protected resource metadata requested from {request.client.host if request.client else 'unknown'}")
    
    response = JSONResponse(content=oauth_config.get_protected_resource_metadata())
    
    # Add cache-control headers to prevent caching by ChatGPT
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    return response


async def authorization_server_metadata(request: Request):
    """
    RFC 8414: OAuth 2.0 Authorization Server Metadata
    Returns our OAuth server metadata (not Google's).
    """
    print(f"[OAuth] Authorization server metadata requested from {request.client.host if request.client else 'unknown'}")
    
    try:
        # Return OUR authorization server metadata
        metadata = {
            "issuer": oauth_config.MCP_SERVER_URL,
            "authorization_endpoint": f"{oauth_config.MCP_SERVER_URL}/oauth/authorize",
            "token_endpoint": f"{oauth_config.MCP_SERVER_URL}/oauth/token",
            "jwks_uri": f"{oauth_config.MCP_SERVER_URL}/oauth/jwks.json",
            "registration_endpoint": f"{oauth_config.MCP_SERVER_URL}/.well-known/oauth-authorization-server/register",
            "scopes_supported": ["openid", "email", "profile"],
            "response_types_supported": ["code"],
            "response_modes_supported": ["query"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
            "code_challenge_methods_supported": ["S256"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
        }
        
        print(f"[OAuth] Returning our authorization endpoints:")
        print(f"  - Issuer: {metadata['issuer']}")
        print(f"  - Authorization: {metadata['authorization_endpoint']}")
        print(f"  - Token: {metadata['token_endpoint']}")
        print(f"  - JWKS: {metadata['jwks_uri']}")
        print(f"  - Registration: {metadata['registration_endpoint']}")
        
        response = JSONResponse(content=metadata)
        
        # Add cache-control headers to prevent caching by ChatGPT
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return response
    
    except Exception as e:
        print(f"[OAuth] Error generating authorization server metadata: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "server_error", "error_description": str(e)}
        )


async def dynamic_client_registration(request: Request):
    """
    RFC 7591: OAuth 2.0 Dynamic Client Registration
    Generates and returns our own client credentials.
    """
    print(f"[OAuth] DCR registration request received from {request.client.host if request.client else 'unknown'}")
    
    try:
        # Parse the registration request
        body = await request.json()
        
        redirect_uris = body.get("redirect_uris", [])
        grant_types = body.get("grant_types", ["authorization_code", "refresh_token"])
        response_types = body.get("response_types", ["code"])
        
        print(f"[OAuth] DCR redirect_uris: {redirect_uris}")
        
        # Register new client in our store
        registration = client_store.register_client(
            redirect_uris=redirect_uris,
            grant_types=grant_types,
            response_types=response_types,
            metadata=body
        )
        
        print(f"[OAuth] DCR generated client_id: {registration.client_id}")
        
        # Return RFC 7591 compliant response
        response = JSONResponse(
            content=registration.to_dict(),
            status_code=201
        )
        
        # Add cache-control headers to prevent caching by ChatGPT
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return response
    
    except Exception as e:
        print(f"[OAuth] Error in dynamic client registration: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_client_metadata", "error_description": str(e)}
        )


async def health_check(request: Request):
    """Health check endpoint"""
    return JSONResponse(content={
        "status": "healthy",
        "oauth_configured": bool(oauth_config.GOOGLE_CLIENT_ID and oauth_config.GOOGLE_CLIENT_SECRET),
        "server_url": oauth_config.MCP_SERVER_URL
    })


# Add OAuth routes to the Starlette app's router
oauth_routes = [
    # OAuth discovery endpoints
    Route("/.well-known/oauth-protected-resource", protected_resource_metadata, methods=["GET"]),
    Route("/.well-known/oauth-authorization-server", authorization_server_metadata, methods=["GET"]),
    Route("/.well-known/oauth-authorization-server/register", dynamic_client_registration, methods=["POST"]),
    
    # OAuth proxy endpoints
    Route("/oauth/authorize", authorization_endpoint, methods=["GET"]),
    Route("/oauth/callback", oauth_callback, methods=["GET"]),
    Route("/oauth/token", token_endpoint, methods=["POST"]),
    Route("/oauth/jwks.json", jwks_endpoint, methods=["GET"]),
    
    # Utility endpoints
    Route("/health", health_check, methods=["GET"]),
]

# Add routes to the router (prepend so they're checked first)
if hasattr(app, 'router') and hasattr(app.router, 'routes'):
    # Insert at the beginning so OAuth routes are checked first
    for route in reversed(oauth_routes):
        app.router.routes.insert(0, route)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# Authentication Middleware removed - all tools now support noauth
# OAuth endpoints remain available for future use if needed


if __name__ == "__main__":
    import uvicorn
    
    # Validate OAuth configuration
    print("\n" + "="*70)
    print("Chess MCP Server with OAuth 2.1 Authorization Server Proxy")
    print("="*70)
    
    try:
        oauth_config.validate()
        print("✓ OAuth configuration validated")
        print(f"✓ Server URL: {oauth_config.MCP_SERVER_URL}")
        print(f"✓ Google Client ID: {oauth_config.GOOGLE_CLIENT_ID[:30]}...")
        print(f"✓ JWT Key ID: {jwt_key_manager.key_id}")
        
        print("\n📋 OAuth Discovery Endpoints:")
        print(f"  - Protected Resource: {oauth_config.MCP_SERVER_URL}/.well-known/oauth-protected-resource")
        print(f"  - Auth Server Metadata: {oauth_config.MCP_SERVER_URL}/.well-known/oauth-authorization-server")
        print(f"  - DCR Registration: {oauth_config.MCP_SERVER_URL}/.well-known/oauth-authorization-server/register")
        
        print("\n🔐 OAuth Flow Endpoints:")
        print(f"  - Authorization: {oauth_config.MCP_SERVER_URL}/oauth/authorize")
        print(f"  - Token Exchange: {oauth_config.MCP_SERVER_URL}/oauth/token")
        print(f"  - JWKS (Public Keys): {oauth_config.MCP_SERVER_URL}/oauth/jwks.json")
        print(f"  - OAuth Callback: {oauth_config.MCP_SERVER_URL}/oauth/callback")
        
        print("\n⚙️  Other Endpoints:")
        print(f"  - Health Check: {oauth_config.MCP_SERVER_URL}/health")
        
        print(f"\n💡 Registered Clients: {client_store.count()}")
        print(f"💡 Active Auth Codes: {auth_code_store.count()}")
        
        print("\n⚠️  IMPORTANT: Update Google OAuth redirect URI to:")
        print(f"   {oauth_config.MCP_SERVER_URL}/oauth/callback")
        
    except ValueError as e:
        print(f"\n⚠️  WARNING: OAuth not fully configured")
        print(f"   {e}")
        print(f"\n   Server will start but OAuth endpoints will not function.")
        print(f"   Create server/.env file with GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")
    
    print("\n" + "="*70)
    print(f"🚀 Starting server on http://0.0.0.0:8000")
    print("="*70 + "\n")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

