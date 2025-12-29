/**
 * Conversation History Management Hook
 * Uses localStorage to store conversation history.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  files?: Array<{
    filename: string;
    mime_type: string;
  }>;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
}

const STORAGE_KEY = 'truthseeker_conversations';
const MAX_CONVERSATIONS = 50;

/**
 * Generate unique ID
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}

/**
 * Generate conversation title from message content
 */
function generateTitle(content: string): string {
  // Use first 50 characters as title
  const trimmed = content.trim().replace(/\n/g, ' ');
  if (trimmed.length <= 50) {
    return trimmed;
  }
  return trimmed.slice(0, 47) + '...';
}

export function useConversationHistory() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load conversation history from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setConversations(parsed);
      }
    } catch (error) {
    }
    setIsLoaded(true);
  }, []);

  // Save to localStorage
  useEffect(() => {
    if (isLoaded) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
      } catch (error) {
      }
    }
  }, [conversations, isLoaded]);

  /**
   * Get current conversation
   */
  const currentConversation = conversations.find(
    conv => conv.id === currentConversationId
  );

  /**
   * Create new conversation
   */
  const createConversation = useCallback((firstMessage?: string, defaultTitle: string = 'New Chat'): string => {
    const newConv: Conversation = {
      id: generateId(),
      title: firstMessage ? generateTitle(firstMessage) : defaultTitle,
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };

    setConversations(prev => {
      // Limit maximum number of conversations
      const updated = [newConv, ...prev].slice(0, MAX_CONVERSATIONS);
      return updated;
    });

    setCurrentConversationId(newConv.id);
    return newConv.id;
  }, []);

  /**
   * Add message to conversation
   */
  const addMessage = useCallback((
    conversationId: string,
    role: 'user' | 'assistant',
    content: string,
    files?: Array<{ filename: string; mime_type: string }>
  ): string => {
    const messageId = generateId();
    const message: Message = {
      id: messageId,
      role,
      content,
      timestamp: Date.now(),
      files,
    };

    setConversations(prev => prev.map(conv => {
      if (conv.id !== conversationId) return conv;

      const updatedConv = {
        ...conv,
        messages: [...conv.messages, message],
        updatedAt: Date.now(),
      };

      // Update title if it's the first user message
      if (role === 'user' && conv.messages.length === 0) {
        // Prefer message content, fallback to first filename
        const titleSource = content || (files && files.length > 0 ? files[0].filename : '');
        if (titleSource) {
          updatedConv.title = generateTitle(titleSource);
        }
      }

      return updatedConv;
    }));

    return messageId;
  }, []);

  /**
   * Update message content
   */
  const updateMessage = useCallback((
    conversationId: string,
    messageId: string,
    content: string
  ) => {
    setConversations(prev => prev.map(conv => {
      if (conv.id !== conversationId) return conv;

      return {
        ...conv,
        messages: conv.messages.map(msg => {
          if (msg.id !== messageId) return msg;
          return { ...msg, content };
        }),
        updatedAt: Date.now(),
      };
    }));
  }, []);

  /**
   * Delete conversation
   */
  const deleteConversation = useCallback((conversationId: string) => {
    setConversations(prev => prev.filter(conv => conv.id !== conversationId));

    if (currentConversationId === conversationId) {
      setCurrentConversationId(null);
    }
  }, [currentConversationId]);

  /**
   * Switch to specified conversation
   */
  const switchConversation = useCallback((conversationId: string | null) => {
    setCurrentConversationId(conversationId);
  }, []);

  /**
   * Clear all conversations
   */
  const clearAllConversations = useCallback(() => {
    setConversations([]);
    setCurrentConversationId(null);
  }, []);

  /**
   * Get conversation history format for API
   */
  const getApiHistory = useCallback((conversationId: string) => {
    const conv = conversations.find(c => c.id === conversationId);
    if (!conv) return [];

    return conv.messages.map(msg => ({
      role: msg.role === 'assistant' ? 'model' : 'user',
      content: msg.content,
    }));
  }, [conversations]);

  return {
    conversations,
    currentConversation,
    currentConversationId,
    isLoaded,
    createConversation,
    addMessage,
    updateMessage,
    deleteConversation,
    switchConversation,
    clearAllConversations,
    getApiHistory,
  };
}
