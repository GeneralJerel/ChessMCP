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
    lastDepth: 15,
    analysisVisible: false,
  });

  // Local component state
  const [position, setPosition] = useState<string>("start");
  const [moveHistory, setMoveHistory] = useState<string[]>([]);
  const [gameStatus, setGameStatus] = useState<string>("ongoing");
  const [currentTurn, setCurrentTurn] = useState<string>("white");
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Chess instance for local validation
  const chess = useMemo(() => new Chess(), []);

  // Update board when tool output changes
  useEffect(() => {
    if (toolOutput) {
      if (toolOutput.fen) {
        setPosition(toolOutput.fen);
        chess.load(toolOutput.fen);
      }
      if (toolOutput.status) {
        setGameStatus(toolOutput.status);
      }
      if (toolOutput.turn) {
        setCurrentTurn(toolOutput.turn);
      }
    }
  }, [toolOutput, chess]);

  // Handle piece drop - validate move and send to chat
  const onPieceDrop = (sourceSquare: string, targetSquare: string) => {
    try {
      // Try to make the move
      const move = chess.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q' // Always promote to queen for simplicity
      });

      if (move === null) {
        // Illegal move
        return false;
      }

      // Send move to chat as user message
      if (window.openai?.sendFollowUpMessage) {
        window.openai.sendFollowUpMessage({ 
          prompt: move.san // Send move in algebraic notation (e.g., "e4", "Nf3")
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

  // Request Stockfish analysis
  const handleStockfishAnalysis = async () => {
    if (!window.openai?.callTool) {
      console.error("window.openai.callTool not available");
      return;
    }

    setIsAnalyzing(true);
    setAnalysis(null);

    try {
      const depth = widgetState?.lastDepth || 15;
      const result = await window.openai.callTool("chess_stockfish", { depth });

      if (result?.content?.[0]?.text) {
        setAnalysis(result.content[0].text);
      } else if (result?.structuredContent?.best_move) {
        const move = result.structuredContent.best_move;
        const eval_text = result.structuredContent.evaluation;
        setAnalysis(`Best move: ${move} (${eval_text})`);
      }

      // Update widget state
      setWidgetState({ ...widgetState, analysisVisible: true });
    } catch (error) {
      console.error("Error calling Stockfish:", error);
      setAnalysis("Error analyzing position");
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
          arePiecesDraggable={true}
          onPieceDrop={onPieceDrop}
          boardWidth={Math.min(560, window.innerWidth - 80)}
        />
      </div>

      {/* Stockfish Analysis Button */}
      <div style={{ marginBottom: "20px", textAlign: "center" }}>
        <button
          onClick={handleStockfishAnalysis}
          disabled={
            isAnalyzing || gameStatus === "checkmate" || gameStatus === "stalemate"
          }
          style={{
            padding: "12px 24px",
            fontSize: "16px",
            fontWeight: "600",
            backgroundColor: theme === "dark" ? "#4a9eff" : "#0066cc",
            color: "#ffffff",
            border: "none",
            borderRadius: "6px",
            cursor: isAnalyzing ? "wait" : "pointer",
            opacity:
              isAnalyzing ||
              gameStatus === "checkmate" ||
              gameStatus === "stalemate"
                ? 0.6
                : 1,
            transition: "all 0.2s",
          }}
          onMouseOver={(e) => {
            if (
              !isAnalyzing &&
              gameStatus !== "checkmate" &&
              gameStatus !== "stalemate"
            ) {
              e.currentTarget.style.backgroundColor =
                theme === "dark" ? "#5aafff" : "#0052a3";
            }
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.backgroundColor =
              theme === "dark" ? "#4a9eff" : "#0066cc";
          }}
        >
          {isAnalyzing ? "Analyzing..." : "Ask Stockfish"}
        </button>
      </div>

      {/* Analysis Result */}
      {analysis && (
        <div
          style={{
            padding: "12px",
            backgroundColor: theme === "dark" ? "#2a4a2a" : "#e8f5e9",
            borderRadius: "6px",
            marginBottom: "20px",
            fontSize: "14px",
          }}
        >
          <strong>Engine Analysis:</strong> {analysis}
        </div>
      )}

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
            {formattedMoveHistory.map((move, index) => (
              <div
                key={index}
                style={{
                  padding: "4px 8px",
                  backgroundColor:
                    index === formattedMoveHistory.length - 1
                      ? theme === "dark"
                        ? "#3a3a3a"
                        : "#e0e0e0"
                      : "transparent",
                  borderRadius: "4px",
                }}
              >
                {move}
              </div>
            ))}
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
          <li>Drag and drop pieces to make a move</li>
          <li>Or type your move in chat (e.g., "e4", "Nf3", "O-O")</li>
          <li>ChatGPT can suggest the next move</li>
          <li>Click "Ask Stockfish" for engine analysis</li>
          <li>Use "chess_status" to check game info</li>
          <li>Use "chess_puzzle" for tactical training</li>
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

