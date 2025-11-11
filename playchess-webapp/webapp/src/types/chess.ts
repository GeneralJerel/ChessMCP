/**
 * Type definitions for the chess webapp
 */

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

export interface ChatResponse {
  response: string;
  metadata: Record<string, any>;
  success: boolean;
}

export interface GameState {
  position: string; // FEN notation
  moveHistory: string[]; // Moves in algebraic notation
  currentTurn: 'white' | 'black';
  status: 'ongoing' | 'check' | 'checkmate' | 'stalemate' | 'draw';
}

export interface Move {
  from: string;
  to: string;
  promotion?: string;
}

