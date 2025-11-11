# Chess Webapp

React-based chess webapp with drag-and-drop gameplay and AI assistant powered by Google ADK.

## Features

- 🎮 Interactive chess board with drag-and-drop
- 💬 Chat with AI assistant for chess help
- 📝 Move history tracking
- 🎨 Lichess-inspired UI
- ⚡ Fast Vite development server

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

The app will be available at http://localhost:5173

## Development

The webapp communicates with the backend API running on port 8001. Make sure the backend is running:

```bash
cd ../webapp-backend
python3 main.py
```

## Project Structure

```
src/
├── components/      # React components
│   ├── ChessBoard.tsx
│   ├── SidePanel.tsx
│   ├── MovesTab.tsx
│   ├── ChatTab.tsx
│   └── ChatMessage.tsx
├── hooks/          # Custom React hooks
│   ├── useChessGame.ts
│   └── useAgentChat.ts
├── services/       # API services
│   └── api.ts
├── types/          # TypeScript types
│   └── chess.ts
├── App.tsx         # Main app component
├── main.tsx        # Entry point
└── index.css       # Global styles
```

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Tech Stack

- React 18
- TypeScript
- Vite
- Tailwind CSS
- chess.js
- react-chessboard
- axios

