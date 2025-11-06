/**
 * Chat Tab Component
 * Chat interface for interacting with the ADK agent
 */

import { useState, useRef, useEffect } from 'react';
import { useAgentChat } from '../hooks/useAgentChat';
import { ChatMessage } from './ChatMessage';

export function ChatTab() {
  const [input, setInput] = useState('');
  const { messages, loading, error, sendMessage, resetConversation } = useAgentChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    await sendMessage(input);
    setInput('');
  };

  const handleReset = async () => {
    if (confirm('Reset conversation? This will clear all messages.')) {
      await resetConversation();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b bg-gray-50 flex justify-between items-center">
        <h3 className="font-semibold text-gray-900">Chess Assistant</h3>
        <button
          onClick={handleReset}
          className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
        >
          Reset
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg mb-2">👋 Welcome!</p>
            <p className="text-sm">
              I'm your chess assistant. Ask me to make moves, analyze positions, or help you learn chess!
            </p>
            <div className="mt-4 text-left bg-blue-50 p-4 rounded-lg">
              <p className="font-semibold mb-2 text-sm">Try saying:</p>
              <ul className="text-sm space-y-1 text-gray-700">
                <li>• "Let's play chess! I'll start with e4"</li>
                <li>• "What's the best move in this position?"</li>
                <li>• "Analyze this position with Stockfish"</li>
                <li>• "Show me a chess puzzle"</li>
              </ul>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}

        {error && (
          <div className="text-red-600 text-sm p-2 bg-red-50 rounded">
            Error: {error}
          </div>
        )}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 text-gray-900 rounded-lg px-4 py-2">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t bg-white">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}

