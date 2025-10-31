/**
 * Product context for global state management
 */

import React, { createContext, useContext, useState, ReactNode } from 'react';
import type { ProductData, ChatMessage } from '@/types';

interface ProductContextType {
  productData: ProductData | null;
  setProductData: (data: ProductData | null) => void;
  analysis: string | null;
  setAnalysis: (analysis: string | null) => void;
  sessionId: string;
  chatHistory: ChatMessage[];
  setChatHistory: (history: ChatMessage[]) => void;
  addChatMessage: (message: ChatMessage) => void;
  removeTypingIndicator: () => void;
  clearChat: () => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
}

const ProductContext = createContext<ProductContextType | undefined>(undefined);

// Generate unique session ID
const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export const ProductProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [productData, setProductData] = useState<ProductData | null>(null);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [sessionId] = useState<string>(generateSessionId());
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const addChatMessage = (message: ChatMessage) => {
    setChatHistory((prev) => [...prev, message]);
  };

  const removeTypingIndicator = () => {
    setChatHistory((prev) => prev.filter(msg => msg.content !== '___TYPING___'));
  };

  const clearChat = () => {
    setChatHistory([]);
  };

  const value: ProductContextType = {
    productData,
    setProductData,
    analysis,
    setAnalysis,
    sessionId,
    chatHistory,
    setChatHistory,
    addChatMessage,
    removeTypingIndicator,
    clearChat,
    isLoading,
    setIsLoading,
    error,
    setError,
  };

  return <ProductContext.Provider value={value}>{children}</ProductContext.Provider>;
};

export const useProduct = (): ProductContextType => {
  const context = useContext(ProductContext);
  if (context === undefined) {
    throw new Error('useProduct must be used within a ProductProvider');
  }
  return context;
};
