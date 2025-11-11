/**
 * Chat Message Component
 * Displays a single chat message
 */

import type { ChatMessage as ChatMessageType } from '../types/chess';

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-primary text-white'
            : 'bg-gray-200 text-gray-900'
        }`}
      >
        <div className="text-sm font-medium mb-1">
          {isUser ? 'You' : 'Chess Assistant'}
        </div>
        <div className="text-base whitespace-pre-wrap break-words">
          {message.content}
        </div>
        {message.timestamp && (
          <div className="text-xs mt-1 opacity-70">
            {message.timestamp.toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
}

