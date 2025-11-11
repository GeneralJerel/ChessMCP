/**
 * Chess Board Component
 * Interactive chess board with drag-and-drop functionality
 */

import { Chessboard } from 'react-chessboard';
import type { Square } from 'chess.js';

interface ChessBoardProps {
  position: string;
  onMove: (from: string, to: string) => boolean;
  disabled?: boolean;
}

export function ChessBoard({ position, onMove, disabled = false }: ChessBoardProps) {
  const handleDrop = (sourceSquare: Square, targetSquare: Square) => {
    if (disabled) return false;
    
    const success = onMove(sourceSquare, targetSquare);
    return success;
  };

  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className="shadow-2xl rounded-lg overflow-hidden">
        <Chessboard
          position={position}
          onPieceDrop={handleDrop}
          boardWidth={600}
          customBoardStyle={{
            borderRadius: '4px',
          }}
          customDarkSquareStyle={{
            backgroundColor: '#b58863',
          }}
          customLightSquareStyle={{
            backgroundColor: '#f0d9b5',
          }}
          arePiecesDraggable={!disabled}
        />
      </div>
    </div>
  );
}

