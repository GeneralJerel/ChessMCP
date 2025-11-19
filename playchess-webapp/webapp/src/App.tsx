/**
 * Main App Component
 * Chess webapp with board and side panel
 */

import { useChessGame } from './hooks/useChessGame';
import { ChessBoard } from './components/ChessBoard';
import { SidePanel } from './components/SidePanel';

export function App() {
  const { position, moveHistory, makeMove, status, currentTurn, reset } = useChessGame();

  const handleMove = (from: string, to: string) => {
    const success = makeMove({ from, to });
    return success;
  };

  const getStatusText = () => {
    switch (status) {
      case 'checkmate':
        return `Checkmate! ${currentTurn === 'white' ? 'Black' : 'White'} wins!`;
      case 'stalemate':
        return 'Stalemate - Draw';
      case 'check':
        return `Check! ${currentTurn === 'white' ? "White" : "Black"}'s turn`;
      case 'draw':
        return 'Draw';
      default:
        return `${currentTurn === 'white' ? "White" : "Black"}'s turn`;
    }
  };

  const isGameOver = status === 'checkmate' || status === 'stalemate' || status === 'draw';

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-100 to-gray-200">
      {/* Left side - Chess board */}
      <div className="flex-1 flex flex-col items-center justify-center p-4">
        <div className="mb-6 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            ♟️ Chess with AI
          </h1>
          <p className="text-gray-600">
            Play chess and chat with your AI assistant
          </p>
        </div>

        {/* Status bar */}
        <div className="mb-4 px-6 py-3 bg-white rounded-lg shadow-md">
          <p className="text-lg font-semibold text-gray-800">
            {getStatusText()}
          </p>
        </div>

        <ChessBoard
          position={position}
          onMove={handleMove}
          disabled={isGameOver}
        />

        {/* Controls */}
        <div className="mt-6 flex space-x-4">
          <button
            onClick={reset}
            className="px-6 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 transition-colors shadow-md"
          >
            New Game
          </button>
        </div>

        {isGameOver && (
          <div className="mt-4 px-6 py-3 bg-yellow-100 border-2 border-yellow-400 rounded-lg">
            <p className="text-yellow-800 font-semibold">
              Game Over! Click "New Game" to play again.
            </p>
          </div>
        )}
      </div>

      {/* Right side - Side panel with tabs */}
      <div className="w-96 h-screen">
        <SidePanel moves={moveHistory} />
      </div>
    </div>
  );
}

