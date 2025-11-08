#!/usr/bin/env python3
"""
Chess MCP Server
Provides chess game functionality via Model Context Protocol
"""

import chess
import chess.pgn
from typing import Optional
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("chess-mcp")

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


def format_move_history(move_history: list) -> str:
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
def chess_stockfish(depth: int = 15, fen: str = None) -> dict:
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
    name="chess_reset",
    title="Reset chess game",
    description="Reset the game to starting position",
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
                "is_puzzle": True
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


# Register the HTML widget resource
@mcp.resource(
    uri="ui://widget/chess-board.html",
    name="Chess Board Widget",
    description="Interactive chess board showing the current game position with move history",
    mime_type="text/html"
)
def get_chess_widget():
    """Return the chess board HTML widget"""
    
    # Load the compiled JavaScript
    js_path = Path(__file__).parent.parent / "web" / "dist" / "chess.js"
    
    if not js_path.exists():
        js_content = "console.error('Chess widget not built. Run: cd web && npm run build');"
    else:
        with open(js_path, "r") as f:
            js_content = f.read()
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        #chess-root {{
            max-width: 600px;
            margin: 0 auto;
        }}
    </style>
</head>
<body>
    <div id="chess-root"></div>
    <script type="module">
        {js_content}
    </script>
</body>
</html>
"""
    
    return html_content


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.get_asgi_app(), host="127.0.0.1", port=3000)

