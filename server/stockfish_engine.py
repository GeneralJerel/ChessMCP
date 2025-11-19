#!/usr/bin/env python3
"""
Stockfish Engine Wrapper
Clean interface for chess engine analysis
"""

import chess
import chess.engine
from pathlib import Path
from typing import Tuple, Optional


class StockfishEngine:
    """Wrapper around Stockfish chess engine"""
    
    def __init__(self, path: str = "/opt/homebrew/bin/stockfish"):
        """
        Initialize Stockfish engine
        
        Args:
            path: Path to Stockfish binary
        """
        self.path = Path(path)
        self._engine: Optional[chess.engine.SimpleEngine] = None
        
        if not self.path.exists():
            raise FileNotFoundError(
                f"Stockfish not found at {path}. "
                "Install with: brew install stockfish (macOS) or apt-get install stockfish (Linux)"
            )
    
    def _get_engine(self) -> chess.engine.SimpleEngine:
        """Get or create engine instance"""
        if self._engine is None:
            self._engine = chess.engine.SimpleEngine.popen_uci(str(self.path))
        return self._engine
    
    def get_best_move(self, fen: str, depth: int = 10) -> Tuple[str, str]:
        """
        Get best move for position
        
        Args:
            fen: Position in FEN notation
            depth: Search depth (default 10)
            
        Returns:
            Tuple of (best_move_uci, evaluation_string)
            - best_move_uci: Move in UCI format (e.g., "e2e4")
            - evaluation_string: Formatted eval (e.g., "+1.5", "M3", "-0.8")
        """
        board = chess.Board(fen)
        engine = self._get_engine()
        
        # Analyze position
        result = engine.analyse(board, chess.engine.Limit(depth=depth))
        
        # Get best move
        best_move = result["pv"][0] if result.get("pv") else None
        if not best_move:
            raise ValueError("Engine returned no best move")
        
        # Format evaluation
        score = result["score"].relative
        if score.is_mate():
            mate_in = score.mate()
            eval_str = f"M{abs(mate_in)}" if mate_in > 0 else f"-M{abs(mate_in)}"
        else:
            centipawns = score.score()
            eval_str = f"{centipawns / 100:+.2f}"
        
        return (best_move.uci(), eval_str)
    
    def close(self):
        """Close engine connection"""
        if self._engine is not None:
            self._engine.quit()
            self._engine = None
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


