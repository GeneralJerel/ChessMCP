/**
 * Chess Board Component for ChatGPT MCP - Simplified
 * Clean, focused widget with no navigation controls
 */

import React, { useEffect, useState, useMemo } from "react";
import { createRoot } from "react-dom/client";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";
import { useOpenAiGlobal } from "../use-openai-global";
import { useToolOutput, useToolResponseMetadata } from "../use-widget-props";
import { useWidgetState } from "../use-widget-state";
import type {
  ChessToolOutput,
  ChessMetadata,
  ChessWidgetState,
} from "../types";

const ChessBoardWidget: React.FC = () => {
  // Use hooks for window.openai access
  const theme = useOpenAiGlobal("theme") || "light";
  const toolOutput = useToolOutput<ChessToolOutput>();
  const toolResponseMetadata = useToolResponseMetadata<ChessMetadata>();

  // Minimal widget state
  const [widgetState, setWidgetState] = useWidgetState<ChessWidgetState>({
    lastPosition: "start",
  });

  // Local component state
  const [position, setPosition] = useState<string>(() => {
    return widgetState?.lastPosition || "start";
  });
  const [moveHistory, setMoveHistory] = useState<string[]>([]);
  const [gameStatus, setGameStatus] = useState<string>("ongoing");
  const [currentTurn, setCurrentTurn] = useState<string>("white");
  const [selectedSquare, setSelectedSquare] = useState<string | null>(null);
  const [highlightedSquares, setHighlightedSquares] = useState<{[square: string]: any}>({});

  // Chess instance for local validation
  const chess = useMemo(() => new Chess(), []);

  // Calculate legal moves for a square
  const getMoveOptions = (square: string) => {
    const moves = chess.moves({ square: square as any, verbose: true }) as any[];
    if (moves.length === 0) {
      return {};
    }

    const newSquares: {[key: string]: any} = {};
    moves.forEach((move: any) => {
      newSquares[move.to] = {
        background: "radial-gradient(circle, rgba(0,0,0,.1) 25%, transparent 25%)",
        borderRadius: "50%"
      };
    });
    return newSquares;
  };

  // Handle square click for piece selection
  const onSquareClick = (square: string) => {
    // If no square selected, select this square and show legal moves
    if (!selectedSquare) {
      const moves = getMoveOptions(square);
      if (Object.keys(moves).length > 0) {
        setSelectedSquare(square);
        setHighlightedSquares(moves);
      }
      return;
    }

    // If clicking same square, deselect
    if (selectedSquare === square) {
      setSelectedSquare(null);
      setHighlightedSquares({});
      return;
    }

    // If clicking a highlighted destination square, make the move
    if (highlightedSquares[square]) {
      const currentFen = chess.fen();
      
      const move = chess.move({
        from: selectedSquare,
        to: square,
        promotion: 'q'
      });

      if (move) {
        chess.undo(); // Server is source of truth
        
        setSelectedSquare(null);
        setHighlightedSquares({});

        // Call apply_move tool with move history
        if (window.openai?.callTool) {
          window.openai.callTool("apply_move", { 
            move: move.san,
            fen: currentFen,
            move_history: JSON.stringify(moveHistory)
          });
        }
      }
      return;
    }

    // Otherwise, check if clicking another piece (switch selection)
    const newMoves = getMoveOptions(square);
    if (Object.keys(newMoves).length > 0) {
      setSelectedSquare(square);
      setHighlightedSquares(newMoves);
    } else {
      setSelectedSquare(null);
      setHighlightedSquares({});
    }
  };

  // Update board when tool output changes
  useEffect(() => {
    if (toolOutput) {
      if (toolOutput.fen) {
        setPosition(toolOutput.fen);
        chess.load(toolOutput.fen);
        setSelectedSquare(null);
        setHighlightedSquares({});
        setWidgetState(prev => ({ ...prev, lastPosition: toolOutput.fen }));
      }
      if (toolOutput.status) {
        setGameStatus(toolOutput.status);
      }
      if (toolOutput.turn) {
        setCurrentTurn(toolOutput.turn);
      }
      if (toolOutput.move_list !== undefined) {
        setMoveHistory(toolOutput.move_list);
      }
    }
  }, [toolOutput]);

  // Handle piece drop - validate move and send to server
  const onPieceDrop = (sourceSquare: string, targetSquare: string) => {
    try {
      const currentFen = chess.fen();
      
      const move = chess.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q'
      });

      if (move === null) {
        return false;
      }

      chess.undo(); // Server is source of truth
      
      setSelectedSquare(null);
      setHighlightedSquares({});

      // Call apply_move tool with move history
      if (window.openai?.callTool) {
        window.openai.callTool("apply_move", { 
          move: move.san,
          fen: currentFen,
          move_history: JSON.stringify(moveHistory)
        });
      }

      return true;
    } catch (error) {
      console.error("Error making move:", error);
      return false;
    }
  };

  // Update move history from metadata
  useEffect(() => {
    if (toolResponseMetadata?.move_history_list) {
      setMoveHistory(toolResponseMetadata.move_history_list);
    }
  }, [toolResponseMetadata]);

  // Get status display text
  const getStatusText = () => {
    switch (gameStatus) {
      case "checkmate":
        return `Checkmate! ${currentTurn === "white" ? "Black" : "White"} wins`;
      case "stalemate":
        return "Stalemate - Draw";
      case "check":
        return `Check! ${currentTurn === "white" ? "White" : "Black"} to move`;
      case "draw_insufficient_material":
        return "Draw - Insufficient material";
      case "puzzle":
        return "Puzzle: Find the mate in 1!";
      default:
        return `${currentTurn === "white" ? "White" : "Black"} to move`;
    }
  };

  // Board styling
  const boardOrientation = "white";
  const darkSquareColor = "#b58863";
  const lightSquareColor = "#f0d9b5";

  // Combine highlighted squares with selected square highlight
  const customSquareStyles = {
    ...highlightedSquares,
    ...(selectedSquare && {
      [selectedSquare]: { backgroundColor: "rgba(255, 255, 0, 0.4)" }
    })
  };

  return (
    <div
      style={{
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        padding: "20px",
        maxWidth: "600px",
        margin: "0 auto",
        backgroundColor: theme === "dark" ? "#1a1a1a" : "#ffffff",
        color: theme === "dark" ? "#ffffff" : "#000000",
        borderRadius: "8px",
      }}
    >
      {/* Game Status */}
      <div
        style={{
          textAlign: "center",
          fontSize: "18px",
          fontWeight: "600",
          marginBottom: "16px",
          padding: "12px",
          backgroundColor: theme === "dark" ? "#2a2a2a" : "#f5f5f5",
          borderRadius: "6px",
        }}
      >
        {getStatusText()}
      </div>

      {/* Chess Board */}
      <div style={{ marginBottom: "20px" }}>
        <Chessboard
          position={position}
          boardOrientation={boardOrientation}
          customDarkSquareStyle={{ backgroundColor: darkSquareColor }}
          customLightSquareStyle={{ backgroundColor: lightSquareColor }}
          customSquareStyles={customSquareStyles}
          arePiecesDraggable={true}
          onPieceDrop={onPieceDrop}
          onSquareClick={onSquareClick}
          boardWidth={Math.min(560, window.innerWidth - 80)}
        />
      </div>

      {/* Move History - Read Only */}
      {moveHistory.length > 0 && (
        <div
          style={{
            marginTop: "20px",
            padding: "16px",
            backgroundColor: theme === "dark" ? "#2a2a2a" : "#f5f5f5",
            borderRadius: "6px",
          }}
        >
          <h3
            style={{
              margin: "0 0 12px 0",
              fontSize: "16px",
              fontWeight: "600",
            }}
          >
            Moves
          </h3>
          <div
            style={{
              fontSize: "14px",
              lineHeight: "1.6",
              maxHeight: "150px",
              overflowY: "auto",
              fontFamily: "monospace",
            }}
          >
            {moveHistory.map((move, moveIndex) => {
              const pairIndex = Math.floor(moveIndex / 2);
              const isWhiteMove = moveIndex % 2 === 0;
              const moveNumber = pairIndex + 1;
              
              return (
                <span key={moveIndex}>
                  {isWhiteMove && (
                    <span
                      style={{
                        color: theme === "dark" ? "#888" : "#666",
                        marginRight: "4px",
                      }}
                    >
                      {moveNumber}.
                    </span>
                  )}
                  <span style={{ marginRight: "4px" }}>
                    {move}
                  </span>
                  {!isWhiteMove && moveIndex < moveHistory.length - 1 && " "}
                  {!isWhiteMove && <br />}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div
        style={{
          marginTop: "20px",
          padding: "12px",
          backgroundColor: theme === "dark" ? "#2a2a3a" : "#f0f4ff",
          borderRadius: "6px",
          fontSize: "13px",
          lineHeight: "1.5",
        }}
      >
        <strong>How to play:</strong>
        <ul style={{ margin: "8px 0 0 0", paddingLeft: "20px" }}>
          <li>Click a piece to see its legal moves</li>
          <li>Drag and drop pieces to make a move</li>
          <li>Or type your move in chat (e.g., "e4", "Nf3", "O-O")</li>
          <li>Say "start a new game" to begin fresh</li>
          <li>Say "give me a puzzle" for practice</li>
        </ul>
      </div>
    </div>
  );
};

// Initialize the widget when the DOM is ready
if (typeof document !== "undefined") {
  const rootElement = document.getElementById("chess-board-root");
  if (rootElement) {
    const root = createRoot(rootElement);
    root.render(<ChessBoardWidget />);
  }
}

export default ChessBoardWidget;
