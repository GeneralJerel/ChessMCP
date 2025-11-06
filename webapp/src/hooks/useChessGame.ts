/**
 * Hook for managing chess game state
 */

import { useState, useCallback } from 'react';
import { Chess } from 'chess.js';
import type { GameState, Move } from '../types/chess';

export function useChessGame() {
  const [chess] = useState(() => new Chess());
  const [position, setPosition] = useState(chess.fen());
  const [moveHistory, setMoveHistory] = useState<string[]>([]);
  const [currentTurn, setCurrentTurn] = useState<'white' | 'black'>('white');
  const [status, setStatus] = useState<GameState['status']>('ongoing');

  const updateGameState = useCallback(() => {
    setPosition(chess.fen());
    setCurrentTurn(chess.turn() === 'w' ? 'white' : 'black');
    
    // Update status
    if (chess.isCheckmate()) {
      setStatus('checkmate');
    } else if (chess.isStalemate()) {
      setStatus('stalemate');
    } else if (chess.isDraw()) {
      setStatus('draw');
    } else if (chess.isCheck()) {
      setStatus('check');
    } else {
      setStatus('ongoing');
    }

    // Update move history
    const history = chess.history();
    setMoveHistory(history);
  }, [chess]);

  const makeMove = useCallback((move: Move | string) => {
    try {
      const result = chess.move(move);
      if (result) {
        updateGameState();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Invalid move:', error);
      return false;
    }
  }, [chess, updateGameState]);

  const reset = useCallback(() => {
    chess.reset();
    updateGameState();
  }, [chess, updateGameState]);

  const loadPosition = useCallback((fen: string) => {
    try {
      chess.load(fen);
      updateGameState();
      return true;
    } catch (error) {
      console.error('Invalid FEN:', error);
      return false;
    }
  }, [chess, updateGameState]);

  const undoMove = useCallback(() => {
    chess.undo();
    updateGameState();
  }, [chess, updateGameState]);

  return {
    position,
    moveHistory,
    currentTurn,
    status,
    makeMove,
    reset,
    loadPosition,
    undoMove,
    chess,
  };
}

