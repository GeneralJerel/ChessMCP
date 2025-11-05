/**
 * Chess Board Component for ChatGPT MCP
 */

import React, { useEffect, useState, useMemo } from 'react';
import { createRoot } from 'react-dom/client';
import { Chess } from 'chess.js';
import { Chessboard } from 'react-chessboard';
import type { ChessToolOutput, ChessMetadata } from './types';

const ChessBoardWidget: React.FC = () => {
  // Get initial state from OpenAI
  const [position, setPosition] = useState<string>('start');
  const [moveHistory, setMoveHistory] = useState<string[]>([]);
  const [gameStatus, setGameStatus] = useState<string>('ongoing');
  const [currentTurn, setCurrentTurn] = useState<string>('white');
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Chess instance for local validation
  const chess = useMemo(() => new Chess(), []);

  // Initialize from window.openai
  useEffect(() => {
    const initializeBoard = () => {
      if (window.openai?.toolOutput) {
        const output = window.openai.toolOutput as ChessToolOutput;
        const metadata = window.openai.toolResponseMetadata as ChessMetadata;

        if (output.fen) {
          setPosition(output.fen);
          chess.load(output.fen);
        }

        if (output.status) {
          setGameStatus(output.status);
        }

        if (output.turn) {
          setCurrentTurn(output.turn);
        }

        if (metadata?.move_history_list) {
          setMoveHistory(metadata.move_history_list);
        }
      }

      if (window.openai?.theme) {
        setTheme(window.openai.theme);
      }
    };

    initializeBoard();

    // Listen for updates
    const handleGlobalsChange = (event: CustomEvent<{ globals: any }>) => {
      const { globals } = event.detail;

      if (globals.toolOutput) {
        const output = globals.toolOutput as ChessToolOutput;
        if (output.fen) {
          setPosition(output.fen);
          chess.load(output.fen);
        }
        if (output.status) setGameStatus(output.status);
        if (output.turn) setCurrentTurn(output.turn);
      }

      if (globals.toolResponseMetadata) {
        const metadata = globals.toolResponseMetadata as ChessMetadata;
        if (metadata.move_history_list) {
          setMoveHistory(metadata.move_history_list);
        }
      }

      if (globals.theme) {
        setTheme(globals.theme);
      }
    };

    window.addEventListener('openai:set_globals', handleGlobalsChange as EventListener);

    return () => {
      window.removeEventListener('openai:set_globals', handleGlobalsChange as EventListener);
    };
  }, [chess]);

  // Request Stockfish analysis
  const handleStockfishAnalysis = async () => {
    if (!window.openai?.callTool) {
      console.error('window.openai.callTool not available');
      return;
    }

    setIsAnalyzing(true);
    setAnalysis(null);

    try {
      const result = await window.openai.callTool('chess_stockfish', { depth: 15 });
      
      if (result?.content?.[0]?.text) {
        setAnalysis(result.content[0].text);
      } else if (result?.structuredContent?.best_move) {
        const move = result.structuredContent.best_move;
        const eval_text = result.structuredContent.evaluation;
        setAnalysis(`Best move: ${move} (${eval_text})`);
      }
    } catch (error) {
      console.error('Error calling Stockfish:', error);
      setAnalysis('Error analyzing position');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Format move history for display
  const formattedMoveHistory = useMemo(() => {
    const formatted: string[] = [];
    for (let i = 0; i < moveHistory.length; i += 2) {
      const moveNum = Math.floor(i / 2) + 1;
      const whiteMove = moveHistory[i];
      const blackMove = moveHistory[i + 1];
      if (blackMove) {
        formatted.push(`${moveNum}. ${whiteMove} ${blackMove}`);
      } else {
        formatted.push(`${moveNum}. ${whiteMove}`);
      }
    }
    return formatted;
  }, [moveHistory]);

  // Get status display text
  const getStatusText = () => {
    switch (gameStatus) {
      case 'checkmate':
        return `Checkmate! ${currentTurn === 'white' ? 'Black' : 'White'} wins`;
      case 'stalemate':
        return 'Stalemate - Draw';
      case 'check':
        return `Check! ${currentTurn === 'white' ? 'White' : 'Black'} to move`;
      case 'draw_insufficient_material':
        return 'Draw - Insufficient material';
      default:
        return `${currentTurn === 'white' ? 'White' : 'Black'} to move`;
    }
  };

  // Determine board orientation (always show from white's perspective by default)
  const boardOrientation = 'white';

  // Board colors based on theme
  const darkSquareColor = theme === 'dark' ? '#b58863' : '#b58863';
  const lightSquareColor = theme === 'dark' ? '#f0d9b5' : '#f0d9b5';

  return (
    <div style={{
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      padding: '20px',
      maxWidth: '600px',
      margin: '0 auto',
      backgroundColor: theme === 'dark' ? '#1a1a1a' : '#ffffff',
      color: theme === 'dark' ? '#ffffff' : '#000000',
      borderRadius: '8px'
    }}>
      {/* Game Status */}
      <div style={{
        textAlign: 'center',
        fontSize: '18px',
        fontWeight: '600',
        marginBottom: '16px',
        padding: '12px',
        backgroundColor: theme === 'dark' ? '#2a2a2a' : '#f5f5f5',
        borderRadius: '6px'
      }}>
        {getStatusText()}
      </div>

      {/* Chess Board */}
      <div style={{ marginBottom: '20px' }}>
        <Chessboard
          position={position}
          boardOrientation={boardOrientation}
          customDarkSquareStyle={{ backgroundColor: darkSquareColor }}
          customLightSquareStyle={{ backgroundColor: lightSquareColor }}
          arePiecesDraggable={false}
          boardWidth={Math.min(560, window.innerWidth - 80)}
        />
      </div>

      {/* Stockfish Analysis Button */}
      <div style={{ marginBottom: '20px', textAlign: 'center' }}>
        <button
          onClick={handleStockfishAnalysis}
          disabled={isAnalyzing || gameStatus === 'checkmate' || gameStatus === 'stalemate'}
          style={{
            padding: '12px 24px',
            fontSize: '16px',
            fontWeight: '600',
            backgroundColor: theme === 'dark' ? '#4a9eff' : '#0066cc',
            color: '#ffffff',
            border: 'none',
            borderRadius: '6px',
            cursor: isAnalyzing ? 'wait' : 'pointer',
            opacity: (isAnalyzing || gameStatus === 'checkmate' || gameStatus === 'stalemate') ? 0.6 : 1,
            transition: 'all 0.2s'
          }}
          onMouseOver={(e) => {
            if (!isAnalyzing && gameStatus !== 'checkmate' && gameStatus !== 'stalemate') {
              e.currentTarget.style.backgroundColor = theme === 'dark' ? '#5aafff' : '#0052a3';
            }
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.backgroundColor = theme === 'dark' ? '#4a9eff' : '#0066cc';
          }}
        >
          {isAnalyzing ? 'Analyzing...' : 'Ask Stockfish'}
        </button>
      </div>

      {/* Analysis Result */}
      {analysis && (
        <div style={{
          padding: '12px',
          backgroundColor: theme === 'dark' ? '#2a4a2a' : '#e8f5e9',
          borderRadius: '6px',
          marginBottom: '20px',
          fontSize: '14px'
        }}>
          <strong>Engine Analysis:</strong> {analysis}
        </div>
      )}

      {/* Move History */}
      {moveHistory.length > 0 && (
        <div style={{
          marginTop: '20px',
          padding: '16px',
          backgroundColor: theme === 'dark' ? '#2a2a2a' : '#f5f5f5',
          borderRadius: '6px'
        }}>
          <h3 style={{
            margin: '0 0 12px 0',
            fontSize: '16px',
            fontWeight: '600'
          }}>
            Move History
          </h3>
          <div style={{
            fontSize: '14px',
            lineHeight: '1.6',
            maxHeight: '150px',
            overflowY: 'auto',
            fontFamily: 'monospace'
          }}>
            {formattedMoveHistory.map((move, index) => (
              <div key={index} style={{
                padding: '4px 8px',
                backgroundColor: index === formattedMoveHistory.length - 1 
                  ? (theme === 'dark' ? '#3a3a3a' : '#e0e0e0')
                  : 'transparent',
                borderRadius: '4px'
              }}>
                {move}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div style={{
        marginTop: '20px',
        padding: '12px',
        backgroundColor: theme === 'dark' ? '#2a2a3a' : '#f0f4ff',
        borderRadius: '6px',
        fontSize: '13px',
        lineHeight: '1.5'
      }}>
        <strong>How to play:</strong>
        <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
          <li>Type your move in chat (e.g., "e4", "Nf3", "O-O")</li>
          <li>ChatGPT can suggest the next move</li>
          <li>Click "Ask Stockfish" for engine analysis</li>
          <li>Type "chess_reset" to start a new game</li>
        </ul>
      </div>
    </div>
  );
};

// Initialize the widget when the DOM is ready
if (typeof document !== 'undefined') {
  const rootElement = document.getElementById('chess-root');
  if (rootElement) {
    const root = createRoot(rootElement);
    root.render(<ChessBoardWidget />);
  }
}

export default ChessBoardWidget;

