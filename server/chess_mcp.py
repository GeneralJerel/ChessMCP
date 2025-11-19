#!/usr/bin/env python3
"""
Clean Chess MCP Server
Minimal, focused API with 6 essential tools
"""

import chess
from pathlib import Path
from functools import lru_cache
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP
import mcp.types as types

from stockfish_engine import StockfishEngine
from puzzle_loader import PuzzleLoader

# Initialize FastMCP
mcp = FastMCP("chess-mcp", stateless_http=True)

# Initialize engine and puzzles
engine = StockfishEngine()
puzzles = PuzzleLoader()

# Assets directory
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

# MIME type for HTML widgets
MIME_TYPE = "text/html+skybridge"


# ============================================================================
# Helper Functions
# ============================================================================

def get_status(board: chess.Board) -> str:
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


def build_response(board: chess.Board, move_list: List[str], extra_content: str = "") -> Dict[str, Any]:
    """
    Build standard response format
    
    Args:
        board: Current chess board
        move_list: List of moves in SAN notation
        extra_content: Optional additional text content
        
    Returns:
        Dictionary with content, structuredContent, and _meta
    """
    status = get_status(board)
    turn = "white" if board.turn == chess.WHITE else "black"
    
    # Build content text
    content_parts = []
    if extra_content:
        content_parts.append(extra_content)
    
    if status == "checkmate":
        winner = "Black" if board.turn == chess.WHITE else "White"
        content_parts.append(f"Checkmate! {winner} wins!")
    elif status == "check":
        content_parts.append(f"Check! {turn.capitalize()} to move")
    elif status == "stalemate":
        content_parts.append("Stalemate - Draw")
    else:
        content_parts.append(f"{turn.capitalize()} to move")
    
    content_text = " ".join(content_parts) if content_parts else f"{turn.capitalize()} to move"
    
    # Get widget metadata with embedded resource
    widget_meta = tool_meta("ui://widget/chess-board.html")
    
    # Merge with additional metadata
    meta = {
        **widget_meta,
        "move_history_list": move_list,
        "legal_moves_count": len(list(board.legal_moves)),
        "is_check": board.is_check(),
        "is_checkmate": board.is_checkmate(),
        "is_stalemate": board.is_stalemate()
    }
    
    return {
        "content": [{"type": "text", "text": content_text}],
        "structuredContent": {
            "fen": board.fen(),
            "status": status,
            "turn": turn,
            "move_list": move_list
        },
        "_meta": meta
    }


@lru_cache(maxsize=None)
def load_widget_html(component_name: str) -> str:
    """Load widget HTML from assets directory (cached)"""
    html_path = ASSETS_DIR / f"{component_name}.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf8")
    
    raise FileNotFoundError(
        f'Widget HTML for "{component_name}" not found in {ASSETS_DIR}. '
        "Run `npm run build` to generate the assets before starting the server."
    )


def embedded_widget_resource() -> types.EmbeddedResource:
    """Create embedded widget resource with HTML content"""
    html = load_widget_html("chess-board")
    return types.EmbeddedResource(
        type="resource",
        resource=types.TextResourceContents(
            uri="ui://widget/chess-board.html",
            mimeType=MIME_TYPE,
            text=html,
            title="Chess Board Widget",
        ),
    )


def tool_meta(uri: str) -> Dict[str, Any]:
    """Generate metadata for tools with embedded widget"""
    widget_resource = embedded_widget_resource()
    return {
        "openai.com/widget": widget_resource.model_dump(mode="json"),
        "openai/outputTemplate": uri,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True
    }


# ============================================================================
# Core MCP Tools (6 Essential Functions)
# ============================================================================

@mcp.tool(
    name="new_game",
    title="Start a new chess game",
    description="Start a fresh chess game and return the starting position",
    annotations={
        "readOnlyHint": False,
        "openai/outputTemplate": "ui://widget/chess-board.html",
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
        "openai/toolInvocation/invoking": "Starting new game...",
        "openai/toolInvocation/invoked": "New game started!"
    }
)
def new_game() -> dict:
    """
    Start a new game
    
    Returns:
        Dictionary with starting position and empty move list
    """
    board = chess.Board()
    return build_response(board, [], "New game started!")


@mcp.tool(
    name="apply_move",
    title="Apply a chess move",
    description="Apply one move in algebraic notation (SAN) to the board",
    annotations={
        "readOnlyHint": False,
        "openai/outputTemplate": "ui://widget/chess-board.html",
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
        "openai/toolInvocation/invoking": "Applying move...",
        "openai/toolInvocation/invoked": "Move applied"
    }
)
def apply_move(move: str, fen: str, move_history: str = None) -> dict:
    """
    Apply a SAN move to the board
    
    Args:
        move: Move in Standard Algebraic Notation (e.g., "e4", "Nf3", "O-O")
        fen: Current position in FEN notation
        move_history: Optional JSON string of previous moves
        
    Returns:
        Dictionary with updated position and move list
    """
    try:
        # Create board from FEN
        board = chess.Board(fen)
        
        # Parse and apply move
        move_obj = board.parse_san(move)
        board.push(move_obj)
        
        # Build move list by adding this move to existing history
        if move_history:
            import json
            try:
                move_list = json.loads(move_history)
            except:
                move_list = []
        else:
            move_list = []
        
        move_list.append(move)
        
        return build_response(board, move_list, f"Played: {move}")
        
    except ValueError as e:
        return {
            "content": [{"type": "text", "text": f"Invalid move: {move}. Error: {str(e)}"}],
            "structuredContent": {"error": str(e), "fen": fen}
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "structuredContent": {"error": str(e), "fen": fen}
        }


@mcp.tool(
    name="engine_move",
    title="Get Stockfish's move",
    description="Get Stockfish's best move and apply it to the board",
    annotations={
        "readOnlyHint": False,
        "openai/outputTemplate": "ui://widget/chess-board.html",
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
        "openai/toolInvocation/invoking": "Stockfish is thinking...",
        "openai/toolInvocation/invoked": "Stockfish has moved!"
    }
)
def engine_move(fen: str, depth: int = 10) -> dict:
    """
    Get and apply Stockfish's best move
    
    Args:
        fen: Current position in FEN notation
        depth: Search depth (default 10)
        
    Returns:
        Dictionary with Stockfish's move, evaluation, and updated position
    """
    try:
        board = chess.Board(fen)
        
        # Get engine move
        best_move_uci, evaluation = engine.get_best_move(fen, depth)
        move_obj = chess.Move.from_uci(best_move_uci)
        best_move_san = board.san(move_obj)
        
        # Apply it
        board.push(move_obj)
        move_list = [board.san(m) for m in board.move_stack]
        
        response = build_response(
            board, 
            move_list, 
            f"Stockfish plays: {best_move_san} (eval: {evaluation})"
        )
        response["structuredContent"]["engine_move"] = best_move_san
        response["structuredContent"]["evaluation"] = evaluation
        response["structuredContent"]["depth"] = depth
        
        return response
        
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Engine error: {str(e)}"}],
            "structuredContent": {"error": str(e), "fen": fen}
        }


@mcp.tool(
    name="analyze",
    title="Analyze position with Stockfish",
    description="Get Stockfish's analysis without making any moves",
    annotations={
        "readOnlyHint": True,
        "openai/toolInvocation/invoking": "Analyzing position...",
        "openai/toolInvocation/invoked": "Analysis complete"
    }
)
def analyze(fen: str, depth: int = 15) -> dict:
    """
    Pure Stockfish analysis - no moves applied
    
    Args:
        fen: Position to analyze in FEN notation
        depth: Search depth (default 15)
        
    Returns:
        Dictionary with best move and evaluation (no board changes)
    """
    try:
        board = chess.Board(fen)
        
        # Get analysis
        best_move_uci, evaluation = engine.get_best_move(fen, depth)
        move_obj = chess.Move.from_uci(best_move_uci)
        best_move_san = board.san(move_obj)
        
        return {
            "content": [{
                "type": "text", 
                "text": f"Best move: {best_move_san}, Evaluation: {evaluation} (depth {depth})"
            }],
            "structuredContent": {
                "best_move": best_move_san,
                "best_move_uci": best_move_uci,
                "evaluation": evaluation,
                "depth": depth,
                "fen": fen
            }
        }
        
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Analysis error: {str(e)}"}],
            "structuredContent": {"error": str(e)}
        }


@mcp.tool(
    name="load_puzzle",
    title="Load a chess puzzle",
    description="Load a mate-in-one puzzle by ID or get a random puzzle",
    annotations={
        "readOnlyHint": False,
        "openai/outputTemplate": "ui://widget/chess-board.html",
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
        "openai/toolInvocation/invoking": "Loading puzzle...",
        "openai/toolInvocation/invoked": "Puzzle loaded!"
    }
)
def load_puzzle(puzzle_id: int = None) -> dict:
    """
    Load a puzzle
    
    Args:
        puzzle_id: Specific puzzle ID, or None for random
        
    Returns:
        Dictionary with puzzle position and metadata
    """
    try:
        puzzle = puzzles.load(puzzle_id)
        board = chess.Board(puzzle["fen"])
        
        puzzle_text = f"Puzzle #{puzzle['id']}: {puzzle['side'].capitalize()} to move and mate in 1!"
        
        return {
            "content": [{"type": "text", "text": puzzle_text}],
            "structuredContent": {
                "fen": puzzle["fen"],
                "puzzle_id": puzzle["id"],
                "side": puzzle["side"],
                "status": "puzzle",
                "turn": puzzle["side"]
            },
            "_meta": {
                "solution": puzzle["solution"],
                "is_puzzle": True,
                "puzzle_id": puzzle["id"],
                "move_history_list": []
            }
        }
        
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error loading puzzle: {str(e)}"}],
            "structuredContent": {"error": str(e)}
        }


@mcp.tool(
    name="check_puzzle_move",
    title="Check puzzle solution",
    description="Check if a move is the correct solution to the puzzle",
    annotations={
        "readOnlyHint": False,
        "openai/outputTemplate": "ui://widget/chess-board.html",
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
        "openai/toolInvocation/invoking": "Checking solution...",
        "openai/toolInvocation/invoked": "Solution checked"
    }
)
def check_puzzle_move(move: str, puzzle_id: int, fen: str) -> dict:
    """
    Check puzzle solution
    
    Args:
        move: Move in SAN notation
        puzzle_id: ID of the puzzle being solved
        fen: Current position
        
    Returns:
        Dictionary indicating if solution is correct
    """
    try:
        puzzle = puzzles.get_by_id(puzzle_id)
        correct = (move.strip() == puzzle["solution"].strip())
        
        if correct:
            # Apply the winning move
            board = chess.Board(fen)
            move_obj = board.parse_san(move)
            board.push(move_obj)
            
            return {
                "content": [{
                    "type": "text", 
                    "text": f"✓ Correct! {move} is the solution!"
                }],
                "structuredContent": {
                    "correct": True,
                    "fen": board.fen(),
                    "solution": move,
                    "status": "checkmate",
                    "puzzle_solved": True
                },
                "_meta": {
                    "puzzle_solved": True,
                    "move_history_list": [move]
                }
            }
        else:
            return {
                "content": [{
                    "type": "text", 
                    "text": f"✗ Incorrect. {move} is not the solution. Try again!"
                }],
                "structuredContent": {
                    "correct": False,
                    "fen": fen,
                    "attempted_move": move,
                    "puzzle_solved": False
                }
            }
            
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error checking solution: {str(e)}"}],
            "structuredContent": {"error": str(e)}
        }


# ============================================================================
# MCP Resource Handler - Simple Decorator Approach
# ============================================================================

@mcp.resource(
    uri="ui://widget/chess-board.html",
    name="Chess Board Widget",
    description="Interactive chess board showing the current game position with move history",
    mime_type=MIME_TYPE
)
def get_chess_widget():
    """Return the chess board HTML widget"""
    html_path = ASSETS_DIR / "chess-board.html"
    
    if not html_path.exists():
        return f"""
<!DOCTYPE html>
<html>
<head><title>Error</title></head>
<body>
<h1>Widget Not Built</h1>
<p>Chess widget not found at {html_path}</p>
<p>Run: <code>npm run build</code> from project root</p>
</body>
</html>
"""
    
    return html_path.read_text(encoding="utf-8")


# ============================================================================
# Server Entry Point
# ============================================================================

# Create ASGI app for stateless HTTP
app = mcp.streamable_http_app()


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Clean Chess MCP Server")
    print("=" * 60)
    print(f"Loaded {puzzles.count()} puzzles")
    print(f"Stockfish engine ready")
    print(f"Serving widget from: {ASSETS_DIR}")
    print("=" * 60)
    print("\n6 Essential MCP Tools:")
    print("  1. new_game - Start fresh game")
    print("  2. apply_move - Apply one move")
    print("  3. engine_move - Get Stockfish move")
    print("  4. analyze - Pure analysis")
    print("  5. load_puzzle - Load puzzle")
    print("  6. check_puzzle_move - Check solution")
    print("=" * 60)
    print("\nStarting server on http://localhost:8000")
    print("Add /mcp endpoint to ChatGPT")
    print("=" * 60)
    
    # Run server with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

