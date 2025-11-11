/**
 * Chess Board Component for ChatGPT MCP
 * Refactored to use OpenAI Apps SDK patterns
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

  // Widget state for persistent preferences
  const [widgetState, setWidgetState] = useWidgetState<ChessWidgetState>({
    lastPosition: "start",
    lastDepth: 15,
    analysisVisible: false,
    currentMoveIndex: null,
  });

  // Local component state - initialize from widgetState first, then toolOutput, then "start"
  const [position, setPosition] = useState<string>(() => {
    if (widgetState?.lastPosition) {
      return widgetState.lastPosition;
    }
    if (toolOutput?.fen) {
      return toolOutput.fen;
    }
    return "start";
  });
  const [moveHistory, setMoveHistory] = useState<string[]>([]);
  const [gameStatus, setGameStatus] = useState<string>("ongoing");
  const [currentTurn, setCurrentTurn] = useState<string>("white");
  const [selectedSquare, setSelectedSquare] = useState<string | null>(null);
  const [highlightedSquares, setHighlightedSquares] = useState<{[square: string]: any}>({});
  const [startingFen, setStartingFen] = useState<string>("start");

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

  // Replay moves up to a specific index
  const replayToMove = (moveIndex: number | null): string => {
    // If moveIndex is null or >= moveHistory.length, return the current position
    if (moveIndex === null || moveIndex >= moveHistory.length) {
      return toolOutput?.fen || startingFen;
    }

    // Create a temporary chess instance
    const tempChess = new Chess();
    
    // Load the starting position
    try {
      if (startingFen === "start") {
        tempChess.reset();
      } else {
        tempChess.load(startingFen);
      }
    } catch (error) {
      console.error("Error loading starting FEN:", error);
      return startingFen;
    }

    // Replay moves up to the specified index (inclusive)
    for (let i = 0; i <= moveIndex && i < moveHistory.length; i++) {
      try {
        tempChess.move(moveHistory[i]);
      } catch (error) {
        console.error(`Error replaying move ${i} (${moveHistory[i]}):`, error);
        break;
      }
    }

    return tempChess.fen();
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
      // Save current position before making the move
      const currentFen = chess.fen();
      
      // Try to make the move locally for validation
      const move = chess.move({
        from: selectedSquare,
        to: square,
        promotion: 'q' // Always promote to queen for simplicity
      });

      if (move) {
        // Undo the local move - the server will handle both moves
        chess.undo();

        // Clear highlights
        setSelectedSquare(null);
        setHighlightedSquares({});

        // Call chess_play_move tool to play against Stockfish
        if (window.openai?.callTool) {
          window.openai.callTool("chess_play_move", { 
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
      // Clicked empty square or opponent piece with no selection - clear
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
        // Update starting FEN for future replays
        // Only update if we're at the current position (not viewing history)
        if (widgetState?.currentMoveIndex === null || widgetState?.currentMoveIndex === undefined) {
          setStartingFen(toolOutput.fen);
        }
        // Clear highlights when board updates
        setSelectedSquare(null);
        setHighlightedSquares({});
        // Persist position in widgetState and reset to current position when new tool output arrives
        setWidgetState(prev => ({ ...prev, lastPosition: toolOutput.fen, currentMoveIndex: null }));
      }
      if (toolOutput.status) {
        setGameStatus(toolOutput.status);
      }
      if (toolOutput.turn) {
        setCurrentTurn(toolOutput.turn);
      }
    }
  }, [toolOutput]);

  // Update position when navigating through move history
  useEffect(() => {
    const moveIndex = widgetState?.currentMoveIndex;
    if (moveHistory.length > 0) {
      const newPosition = replayToMove(moveIndex ?? null);
      setPosition(newPosition);
      chess.load(newPosition);
      // Clear highlights when navigating
      setSelectedSquare(null);
      setHighlightedSquares({});
    }
  }, [widgetState?.currentMoveIndex, moveHistory]);

  // Handle piece drop - validate move and send to chat
  const onPieceDrop = (sourceSquare: string, targetSquare: string) => {
    try {
      // Save current position before making the move
      const currentFen = chess.fen();
      
      // Try to make the move locally for validation
      const move = chess.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q' // Always promote to queen for simplicity
      });

      if (move === null) {
        // Illegal move
        return false;
      }

      // Undo the local move - the server will handle both moves
      chess.undo();

      // Clear highlights
      setSelectedSquare(null);
      setHighlightedSquares({});

      // Call chess_play_move tool to play against Stockfish
      if (window.openai?.callTool) {
        window.openai.callTool("chess_play_move", { 
          move: move.san, // User's move in algebraic notation (e.g., "e4", "Nf3")
          fen: currentFen, // Current position before any moves
          move_history: JSON.stringify(moveHistory) // Send current move history
        });
      }

      // Move was valid
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

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Only handle if we have moves and not typing in an input
      if (moveHistory.length === 0) return;
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (event.key) {
        case "ArrowLeft":
          event.preventDefault();
          goToPrevious();
          break;
        case "ArrowRight":
          event.preventDefault();
          goToNext();
          break;
        case "Home":
          event.preventDefault();
          goToStart();
          break;
        case "End":
          event.preventDefault();
          goToEnd();
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [moveHistory.length, widgetState?.currentMoveIndex]);


  // Navigation functions
  const goToStart = () => {
    setWidgetState({ ...widgetState, currentMoveIndex: -1 });
  };

  const goToPrevious = () => {
    const currentIndex = widgetState?.currentMoveIndex ?? moveHistory.length - 1;
    const newIndex = Math.max(-1, currentIndex - 1);
    setWidgetState({ ...widgetState, currentMoveIndex: newIndex });
  };

  const goToNext = () => {
    const currentIndex = widgetState?.currentMoveIndex ?? moveHistory.length - 1;
    const newIndex = Math.min(moveHistory.length - 1, currentIndex + 1);
    setWidgetState({ ...widgetState, currentMoveIndex: newIndex });
  };

  const goToEnd = () => {
    setWidgetState({ ...widgetState, currentMoveIndex: null });
  };

  const goToMove = (moveIndex: number) => {
    setWidgetState({ ...widgetState, currentMoveIndex: moveIndex });
  };

  // Game control functions
  const handleNewGame = () => {
    if (window.openai?.callTool) {
      window.openai.callTool("chess_reset", {});
    }
  };

  const handleMateInOne = () => {
    if (window.openai?.callTool) {
      window.openai.callTool("chess_puzzle", {});
    }
  };

  // Check if we're viewing a past position
  const isViewingHistory = useMemo(() => {
    const currentIndex = widgetState?.currentMoveIndex;
    return currentIndex !== null && currentIndex !== undefined && currentIndex < moveHistory.length - 1;
  }, [widgetState?.currentMoveIndex, moveHistory.length]);

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

  // Determine board orientation
  const boardOrientation = "white";

  // Board colors based on theme
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
          arePiecesDraggable={!isViewingHistory}
          onPieceDrop={onPieceDrop}
          onSquareClick={onSquareClick}
          boardWidth={Math.min(560, window.innerWidth - 80)}
        />
      </div>

      {/* View-Only Mode Indicator */}
      {isViewingHistory && (
        <div
          style={{
            textAlign: "center",
            fontSize: "14px",
            fontWeight: "500",
            marginBottom: "12px",
            padding: "8px 12px",
            backgroundColor: theme === "dark" ? "#3a3a2a" : "#fff4e6",
            color: theme === "dark" ? "#ffb74d" : "#e65100",
            borderRadius: "6px",
            border: `1px solid ${theme === "dark" ? "#ffb74d" : "#e65100"}`,
          }}
        >
          ⏸ Viewing move {(widgetState?.currentMoveIndex ?? -1) + 1} of {moveHistory.length}
        </div>
      )}

      {/* Navigation Controls */}
      {moveHistory.length > 0 && (
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: "8px",
            marginBottom: "20px",
          }}
        >
          <button
            onClick={goToStart}
            disabled={(widgetState?.currentMoveIndex ?? moveHistory.length) <= -1}
            style={{
              padding: "8px 16px",
              fontSize: "18px",
              backgroundColor: theme === "dark" ? "#2a2a2a" : "#f5f5f5",
              color: theme === "dark" ? "#ffffff" : "#000000",
              border: `1px solid ${theme === "dark" ? "#444" : "#ddd"}`,
              borderRadius: "6px",
              cursor: (widgetState?.currentMoveIndex ?? moveHistory.length) <= -1 ? "not-allowed" : "pointer",
              opacity: (widgetState?.currentMoveIndex ?? moveHistory.length) <= -1 ? 0.5 : 1,
              transition: "all 0.2s",
            }}
            title="Go to start"
          >
            ⏮
          </button>
          <button
            onClick={goToPrevious}
            disabled={(widgetState?.currentMoveIndex ?? moveHistory.length) <= -1}
            style={{
              padding: "8px 16px",
              fontSize: "18px",
              backgroundColor: theme === "dark" ? "#2a2a2a" : "#f5f5f5",
              color: theme === "dark" ? "#ffffff" : "#000000",
              border: `1px solid ${theme === "dark" ? "#444" : "#ddd"}`,
              borderRadius: "6px",
              cursor: (widgetState?.currentMoveIndex ?? moveHistory.length) <= -1 ? "not-allowed" : "pointer",
              opacity: (widgetState?.currentMoveIndex ?? moveHistory.length) <= -1 ? 0.5 : 1,
              transition: "all 0.2s",
            }}
            title="Previous move"
          >
            ◀
          </button>
          <button
            onClick={goToNext}
            disabled={(widgetState?.currentMoveIndex ?? moveHistory.length - 1) >= moveHistory.length - 1}
            style={{
              padding: "8px 16px",
              fontSize: "18px",
              backgroundColor: theme === "dark" ? "#2a2a2a" : "#f5f5f5",
              color: theme === "dark" ? "#ffffff" : "#000000",
              border: `1px solid ${theme === "dark" ? "#444" : "#ddd"}`,
              borderRadius: "6px",
              cursor: (widgetState?.currentMoveIndex ?? moveHistory.length - 1) >= moveHistory.length - 1 ? "not-allowed" : "pointer",
              opacity: (widgetState?.currentMoveIndex ?? moveHistory.length - 1) >= moveHistory.length - 1 ? 0.5 : 1,
              transition: "all 0.2s",
            }}
            title="Next move"
          >
            ▶
          </button>
          <button
            onClick={goToEnd}
            disabled={widgetState?.currentMoveIndex === null || widgetState?.currentMoveIndex === undefined}
            style={{
              padding: "8px 16px",
              fontSize: "18px",
              backgroundColor: theme === "dark" ? "#2a2a2a" : "#f5f5f5",
              color: theme === "dark" ? "#ffffff" : "#000000",
              border: `1px solid ${theme === "dark" ? "#444" : "#ddd"}`,
              borderRadius: "6px",
              cursor: widgetState?.currentMoveIndex === null || widgetState?.currentMoveIndex === undefined ? "not-allowed" : "pointer",
              opacity: widgetState?.currentMoveIndex === null || widgetState?.currentMoveIndex === undefined ? 0.5 : 1,
              transition: "all 0.2s",
            }}
            title="Go to current position"
          >
            ⏭
          </button>
        </div>
      )}

      {/* Game Control Buttons */}
      <div style={{ display: "flex", justifyContent: "center", gap: "12px", marginBottom: "20px" }}>
        <button
          onClick={handleNewGame}
          style={{
            padding: "12px 24px",
            fontSize: "16px",
            fontWeight: "600",
            backgroundColor: theme === "dark" ? "#4a9eff" : "#0066cc",
            color: "#ffffff",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            transition: "all 0.2s",
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.backgroundColor =
              theme === "dark" ? "#5aafff" : "#0052a3";
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.backgroundColor =
              theme === "dark" ? "#4a9eff" : "#0066cc";
          }}
        >
          New Game
        </button>
        <button
          onClick={handleMateInOne}
          style={{
            padding: "12px 24px",
            fontSize: "16px",
            fontWeight: "600",
            backgroundColor: theme === "dark" ? "#ff8a65" : "#ff6f00",
            color: "#ffffff",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            transition: "all 0.2s",
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.backgroundColor =
              theme === "dark" ? "#ff9575" : "#e65100";
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.backgroundColor =
              theme === "dark" ? "#ff8a65" : "#ff6f00";
          }}
        >
          Mate in 1
        </button>
      </div>

      {/* Move History */}
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
            Move History
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
              const currentIndex = widgetState?.currentMoveIndex ?? moveHistory.length - 1;
              const isCurrentMove = moveIndex === currentIndex;
              
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
                  <span
                    onClick={() => goToMove(moveIndex)}
                    style={{
                      padding: "2px 6px",
                      marginRight: "4px",
                      backgroundColor: isCurrentMove
                        ? theme === "dark"
                          ? "#4a9eff"
                          : "#0066cc"
                        : "transparent",
                      color: isCurrentMove
                        ? "#ffffff"
                        : theme === "dark"
                        ? "#ffffff"
                        : "#000000",
                      borderRadius: "3px",
                      cursor: "pointer",
                      transition: "all 0.2s",
                    }}
                    onMouseOver={(e) => {
                      if (!isCurrentMove) {
                        e.currentTarget.style.backgroundColor =
                          theme === "dark" ? "#3a3a3a" : "#e0e0e0";
                      }
                    }}
                    onMouseOut={(e) => {
                      if (!isCurrentMove) {
                        e.currentTarget.style.backgroundColor = "transparent";
                      }
                    }}
                  >
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
          <li>Use arrow keys (←/→) to navigate through moves</li>
          <li>Click "New Game" to start fresh</li>
          <li>Click "Mate in 1" for puzzle practice</li>
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

