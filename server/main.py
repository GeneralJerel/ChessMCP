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

# OAuth imports
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

# Per-user game state storage (in-memory)
# Key: user email, Value: dict with game state
user_games: Dict[str, Dict[str, Any]] = {}

# Path to stockfish binary (update this path if needed)
STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"  # Common macOS path


def get_user_game(user_email: str) -> Dict[str, Any]:
    """Get or create a game state for a user"""
    if user_email not in user_games:
        user_games[user_email] = {
            "board": chess.Board(),
            "move_history": [],
            "player_white": "You",
            "player_black": "Opponent"
        }
    return user_games[user_email]


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
def chess_move(move: str) -> dict:
    """
    Make a chess move on the board.
    
    Args:
        move: The move in algebraic notation (e.g., "e4", "Nf3", "O-O", "e8=Q")
    
    Returns:
        Dictionary containing the updated game state
    """
    # Get authenticated user
    user = get_current_user()
    if not user:
        return {
            "content": [{"type": "text", "text": "Authentication required"}],
            "structuredContent": {"error": "not_authenticated"}
        }
    
    # Get user's game state
    game_state = get_user_game(user.email)
    current_game = game_state["board"]
    move_history = game_state["move_history"]
    
    try:
        # Try to parse and make the move
        chess_move_obj = current_game.parse_san(move)
        current_game.push(chess_move_obj)
        
        # Add to move history
        move_history.append(move)
        
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
            "move_history": format_move_history(move_history),
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
                "legal_moves": legal_moves[:50],  # Limit for metadata
                "move_history_list": move_history
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
def chess_stockfish(depth: int = 15) -> dict:
    """
    Analyze the current position using Stockfish engine.
    
    Args:
        depth: Analysis depth (default: 15)
    
    Returns:
        Dictionary containing engine analysis and best move
    """
    # Get user-specific game if authenticated, otherwise use default
    user = get_current_user()
    if user:
        game_state = get_user_game(user.email)
        current_game = game_state["board"]
    else:
        # Anonymous access - use a default starting position
        current_game = chess.Board()
    
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
        Dictionary confirming the reset
    """
    # Get authenticated user
    user = get_current_user()
    if not user:
        return {
            "content": [{"type": "text", "text": "Authentication required"}],
            "structuredContent": {"error": "not_authenticated"}
        }
    
    # Reset user's game state
    game_state = get_user_game(user.email)
    game_state["board"] = chess.Board()
    game_state["move_history"] = []
    
    return {
        "content": [{"type": "text", "text": "Chess game reset to starting position"}],
        "structuredContent": {
            "fen": game_state["board"].fen(),
            "status": "ongoing"
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
def chess_status() -> dict:
    """
    Get the current status of the chess game.
    
    Returns:
        Dictionary containing game status, turn, players, and move count
    """
    # Get user-specific game if authenticated, otherwise use default
    user = get_current_user()
    if user:
        game_state = get_user_game(user.email)
        current_game = game_state["board"]
        move_history = game_state["move_history"]
        player_white = game_state["player_white"]
        player_black = game_state["player_black"]
    else:
        # Anonymous access
        current_game = chess.Board()
        move_history = []
        player_white = "Player"
        player_black = "Opponent"
    
    # Get current turn
    turn_color = "White" if current_game.turn == chess.WHITE else "Black"
    turn_player = player_white if current_game.turn == chess.WHITE else player_black
    
    # Get game status
    status = get_game_status(current_game)
    
    # Count moves
    full_moves = current_game.fullmove_number
    half_moves = len(move_history)
    
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
    
    # Add move history summary
    if move_history:
        message += f"\n\n📝 Last 3 moves: {', '.join(move_history[-6:])}"
    
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
            "total_moves": half_moves,
            "fen": current_game.fen(),
            "is_check": current_game.is_check(),
            "is_game_over": current_game.is_game_over()
        },
        "_meta": {
            "move_history": move_history,
            "legal_moves_count": len(list(current_game.legal_moves))
        }
    }


@mcp.tool(
    name="chess_puzzle",
    title="Show mate in 1 puzzle",
    description="Load a mate-in-one puzzle position for the user to solve",
    annotations={
        "readOnlyHint": False,
        "openai/outputTemplate": "ui://widget/chess-board.html",
        "openai/toolInvocation/invoking": "Loading puzzle...",
        "openai/toolInvocation/invoked": "Puzzle loaded"
    }
)
def chess_puzzle(difficulty: str = "easy") -> dict:
    """
    Load a mate-in-one puzzle for the user to solve.
    
    Args:
        difficulty: Puzzle difficulty (easy, medium, hard) - currently loads random positions
    
    Returns:
        Dictionary with puzzle position and instructions
    """
    # Get authenticated user
    user = get_current_user()
    
    if not user:
        return {
            "content": [{"type": "text", "text": "Authentication required"}],
            "structuredContent": {"error": "not_authenticated"}
        }
    
    # Collection of mate-in-1 puzzles (FEN positions where White has mate in 1)
    puzzles = {
        "easy": [
            # Back rank mate
            {
                "fen": "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",
                "solution": "Ra8#",
                "hint": "The black king has no escape on the back rank!"
            },
            # Queen and king mate
            {
                "fen": "7k/5Q2/6K1/8/8/8/8/8 w - - 0 1",
                "solution": "Qg7#",
                "hint": "The queen can deliver checkmate next to the king!"
            },
            # Rook mate
            {
                "fen": "6k1/6p1/5pKp/8/8/8/8/7R w - - 0 1",
                "solution": "Rh8#",
                "hint": "Look at the back rank!"
            },
        ],
        "medium": [
            # Discovery mate
            {
                "fen": "r4rk1/5ppp/8/8/8/2B5/5PPP/4R1K1 w - - 0 1",
                "solution": "Re8#",
                "hint": "Move the rook to deliver mate!"
            },
            # Knight mate
            {
                "fen": "6k1/5ppp/4p3/8/8/8/5PPP/4N1K1 w - - 0 1",
                "solution": "Nf3# or Ne2#",
                "hint": "The knight can jump to deliver mate!"
            },
            # Smothered mate
            {
                "fen": "6rk/6pp/7N/8/8/8/8/6K1 w - - 0 1",
                "solution": "Nf7#",
                "hint": "The king is trapped by its own pieces!"
            },
        ],
        "hard": [
            # Complex position
            {
                "fen": "r3k2r/1b2bppp/p7/1p2B3/3pP3/P2B1P2/1P4PP/R4RK1 w kq - 0 1",
                "solution": "Rf8#",
                "hint": "The king cannot escape the back rank!"
            },
            # Bishop and queen mate
            {
                "fen": "r4rk1/1bq2ppp/p7/1p6/3P4/P2B4/1P2QPPP/R5K1 w - - 0 1",
                "solution": "Qe8#",
                "hint": "The queen can finish the game!"
            },
        ]
    }
    
    # Select puzzle based on difficulty
    import random
    puzzle_set = puzzles.get(difficulty, puzzles["easy"])
    puzzle = random.choice(puzzle_set)
    
    # Load the puzzle position into user's game state
    game_state = get_user_game(user.email)
    game_state["board"] = chess.Board(puzzle["fen"])
    game_state["move_history"] = []
    game_state["player_white"] = "You"
    game_state["player_black"] = "Computer"
    
    # Create message
    message = f"🧩 Mate in 1 Puzzle ({difficulty.capitalize()})\n\n"
    message += f"White to move and checkmate in one move!\n\n"
    message += f"💡 Hint: {puzzle['hint']}\n\n"
    message += f"Try to find the winning move!"
    
    return {
        "content": [{"type": "text", "text": message}],
        "structuredContent": {
            "fen": game_state["board"].fen(),
            "puzzle_type": "mate_in_1",
            "difficulty": difficulty,
            "turn": "white",
            "status": "puzzle"
        },
        "_meta": {
            "solution": puzzle["solution"],
            "hint": puzzle["hint"],
            "is_puzzle": True
        }
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


# Register resources properly
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


# Register the resource handler
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

# Add CORS middleware BEFORE auth (must be outermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# Add Authentication Middleware (will skip MCP protocol endpoints)
app.add_middleware(AuthenticationMiddleware)


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

