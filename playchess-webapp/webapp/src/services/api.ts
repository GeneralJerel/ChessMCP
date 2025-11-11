/**
 * API service for communicating with the backend
 */

import axios from 'axios';
import type { ChatResponse } from '../types/chess';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const chatApi = {
  /**
   * Send a message to the ADK agent
   */
  async sendMessage(message: string, sessionId: string = 'default'): Promise<ChatResponse> {
    try {
      const response = await axios.post<ChatResponse>(`${API_BASE_URL}/chat/message`, {
        message,
        session_id: sessionId,
      });
      return response.data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  },

  /**
   * Check health status
   */
  async healthCheck(): Promise<{ status: string }> {
    const response = await axios.get(`${API_BASE_URL}/chat/health`);
    return response.data;
  },

  /**
   * Reset conversation
   */
  async resetConversation(sessionId: string = 'default'): Promise<void> {
    await axios.post(`${API_BASE_URL}/chat/reset`, { session_id: sessionId });
  },
};

