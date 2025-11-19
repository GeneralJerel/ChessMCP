#!/usr/bin/env python3
"""
Puzzle Database Loader
Clean interface for loading chess puzzles
"""

import csv
import random
from pathlib import Path
from typing import Optional, Dict, List


class PuzzleLoader:
    """Loader for chess puzzles from CSV database"""
    
    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialize puzzle loader
        
        Args:
            csv_path: Path to puzzle CSV file (defaults to data/mate-in-one.csv)
        """
        if csv_path is None:
            csv_path = Path(__file__).parent / "data" / "mate-in-one.csv"
        else:
            csv_path = Path(csv_path)
        
        self.csv_path = csv_path
        self._puzzles: Optional[List[Dict]] = None
        
        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"Puzzle database not found at {csv_path}. "
                "Expected mate-in-one.csv in server/data/ directory."
            )
    
    def _load_puzzles(self) -> List[Dict]:
        """Load puzzles from CSV (cached after first load)"""
        if self._puzzles is None:
            self._puzzles = []
            
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for idx, row in enumerate(reader, start=1):
                    # Parse FEN to determine side to move
                    fen = row.get('fen', '')
                    side = "white" if " w " in fen else "black"
                    
                    puzzle = {
                        "id": int(row.get('id', idx)),
                        "fen": fen,
                        "solution": row.get('solution', '').strip(),
                        "side": side
                    }
                    self._puzzles.append(puzzle)
            
            print(f"Loaded {len(self._puzzles)} puzzles from {self.csv_path}")
        
        return self._puzzles
    
    def load(self, puzzle_id: Optional[int] = None) -> Dict:
        """
        Load a puzzle by ID or random
        
        Args:
            puzzle_id: Specific puzzle ID, or None for random
            
        Returns:
            Dictionary with keys: id, fen, solution, side
        """
        puzzles = self._load_puzzles()
        
        if puzzle_id is not None:
            # Find specific puzzle
            puzzle = next((p for p in puzzles if p["id"] == puzzle_id), None)
            if puzzle is None:
                raise ValueError(f"Puzzle {puzzle_id} not found. Available IDs: 1-{len(puzzles)}")
            return puzzle
        else:
            # Return random puzzle
            return random.choice(puzzles)
    
    def get_by_id(self, puzzle_id: int) -> Dict:
        """
        Get specific puzzle by ID
        
        Args:
            puzzle_id: Puzzle ID
            
        Returns:
            Dictionary with keys: id, fen, solution, side
        """
        return self.load(puzzle_id)
    
    def count(self) -> int:
        """Get total number of puzzles"""
        puzzles = self._load_puzzles()
        return len(puzzles)


