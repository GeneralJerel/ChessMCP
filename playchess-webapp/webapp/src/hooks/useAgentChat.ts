/**
 * Hook for managing chat with the ADK agent
 */

import { useState, useCallback } from 'react';
import { chatApi } from '../services/api';
import type { ChatMessage } from '../types/chess';

export function useAgentChat(sessionId: string = 'default') {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim()) return;

    setLoading(true);
    setError(null);

    // Add user message immediately
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      // Send to backend
      const response = await chatApi.sendMessage(message, sessionId);

      // Add assistant response
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);

      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      
      // Add error message as assistant message
      const errorMsg: ChatMessage = {
        role: 'assistant',
        content: `Error: ${errorMessage}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  const resetConversation = useCallback(async () => {
    try {
      await chatApi.resetConversation(sessionId);
      clearMessages();
    } catch (err) {
      console.error('Error resetting conversation:', err);
    }
  }, [sessionId, clearMessages]);

  return {
    messages,
    loading,
    error,
    sendMessage,
    clearMessages,
    resetConversation,
  };
}

