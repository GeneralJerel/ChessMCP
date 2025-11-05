/**
 * Type definitions for Chess MCP Widget
 */

export interface ChessToolOutput {
  fen: string;
  move: string;
  status: string;
  turn: string;
}

export interface ChessMetadata {
  full_state?: {
    success: boolean;
    move: string;
    fen: string;
    turn: string;
    move_history: string;
    status: string;
    legal_moves_count: number;
    is_check: boolean;
    is_checkmate: boolean;
    is_stalemate: boolean;
  };
  legal_moves?: string[];
  move_history_list?: string[];
}

export interface OpenAIGlobals {
  theme: 'light' | 'dark';
  userAgent: {
    device: { type: string };
    capabilities: { hover: boolean; touch: boolean };
  };
  locale: string;
  maxHeight: number;
  displayMode: 'pip' | 'inline' | 'fullscreen';
  safeArea: {
    insets: {
      top: number;
      bottom: number;
      left: number;
      right: number;
    };
  };
  toolInput: any;
  toolOutput: ChessToolOutput | null;
  toolResponseMetadata: ChessMetadata | null;
  widgetState: any;
}

export interface OpenAIAPI {
  callTool: (name: string, args: Record<string, unknown>) => Promise<any>;
  sendFollowUpMessage: (args: { prompt: string }) => Promise<void>;
  openExternal: (payload: { href: string }) => void;
  requestDisplayMode: (args: { mode: 'pip' | 'inline' | 'fullscreen' }) => Promise<{ mode: string }>;
  setWidgetState: (state: any) => Promise<void>;
}

declare global {
  interface Window {
    openai: OpenAIAPI & OpenAIGlobals;
  }

  interface WindowEventMap {
    'openai:set_globals': CustomEvent<{ globals: Partial<OpenAIGlobals> }>;
  }
}

export {};

