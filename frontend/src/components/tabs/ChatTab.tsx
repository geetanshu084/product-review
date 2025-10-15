/**
 * Chat/Q&A tab component
 */

import React, { useState, useRef, useEffect } from 'react';
import { apiClient } from '@/services/api';
import { useProduct } from '@/contexts/ProductContext';

const ChatTab: React.FC = () => {
  const { productData, sessionId, chatHistory, addChatMessage, clearChat } = useProduct();
  const [question, setQuestion] = useState<string>('');
  const [isAsking, setIsAsking] = useState<boolean>(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!question.trim() || !productData?.asin) {
      return;
    }

    const userQuestion = question.trim();
    setQuestion(''); // Clear input immediately
    setIsAsking(true);

    // Add user message
    addChatMessage({ role: 'user', content: userQuestion });

    try {
      const response = await apiClient.askQuestion({
        session_id: sessionId,
        product_id: productData.asin,
        question: userQuestion,
      });

      if (response.success) {
        addChatMessage({ role: 'assistant', content: response.answer });
      } else {
        addChatMessage({
          role: 'assistant',
          content: 'Sorry, I could not process your question. Please try again.',
        });
      }
    } catch (err: any) {
      addChatMessage({
        role: 'assistant',
        content: 'Sorry, an error occurred. Please try again.',
      });
    } finally {
      setIsAsking(false);
    }
  };

  const handleClearChat = async () => {
    try {
      await apiClient.clearChat({ session_id: sessionId });
      clearChat();
    } catch (err) {
      console.error('Failed to clear chat:', err);
    }
  };

  // Extract URLs from text
  const extractUrls = (text: string): string[] => {
    const urlPattern = /https?:\/\/[^\s<>"{}|\\^`\[\]]+/g;
    return text.match(urlPattern) || [];
  };

  // Detect e-commerce site
  const detectSite = (url: string): { name: string; icon: string } => {
    const urlLower = url.toLowerCase();
    if (urlLower.includes('amazon')) return { name: 'Amazon', icon: '🛒' };
    if (urlLower.includes('flipkart')) return { name: 'Flipkart', icon: '🛍️' };
    if (urlLower.includes('ebay')) return { name: 'eBay', icon: '🏪' };
    return { name: 'Product Link', icon: '🔗' };
  };

  // Format message with clickable links
  const formatMessage = (content: string) => {
    const urls = extractUrls(content);
    let displayText = content;

    // Remove URLs from display text
    urls.forEach((url) => {
      displayText = displayText.replace(url, '');
    });

    return (
      <>
        <p style={styles.messageText}>{displayText}</p>
        {urls.length > 0 && (
          <div style={styles.linksContainer}>
            <strong>🔗 Referenced Links:</strong>
            {urls.map((url, idx) => {
              const { name, icon } = detectSite(url);
              return (
                <a
                  key={idx}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={styles.linkButton}
                >
                  {icon} {name} - Visit →
                </a>
              );
            })}
          </div>
        )}
      </>
    );
  };

  if (!productData) {
    return (
      <div style={styles.emptyState}>
        <p>Please scrape a product first to start asking questions.</p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>💬 Ask Questions About This Product</h3>
        {chatHistory.length > 0 && (
          <button onClick={handleClearChat} style={styles.clearButton}>
            🗑️ Clear Chat
          </button>
        )}
      </div>

      <div style={styles.chatContainer}>
        {chatHistory.length === 0 ? (
          <div style={styles.placeholder}>
            <p>Ask me anything about this product!</p>
            <div style={styles.suggestions}>
              <strong>Example questions:</strong>
              <ul>
                <li>What are the main pros and cons?</li>
                <li>Is this good value for money?</li>
                <li>How does it compare to alternatives?</li>
                <li>What do customers say about durability?</li>
              </ul>
            </div>
          </div>
        ) : (
          <div style={styles.messages}>
            {chatHistory.map((msg, idx) => (
              <div
                key={idx}
                style={
                  msg.role === 'user'
                    ? { ...styles.message, ...styles.userMessage }
                    : { ...styles.message, ...styles.assistantMessage }
                }
              >
                <div style={styles.messageRole}>
                  {msg.role === 'user' ? '👤 You' : '🤖 Assistant'}
                </div>
                {msg.role === 'assistant' ? (
                  formatMessage(msg.content)
                ) : (
                  <p style={styles.messageText}>{msg.content}</p>
                )}
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
        )}
      </div>

      <form onSubmit={handleAsk} style={styles.inputForm}>
        <input
          type="text"
          placeholder="Ask a question about this product..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={isAsking}
          style={styles.input}
        />
        <button
          type="submit"
          disabled={isAsking || !question.trim()}
          style={
            isAsking || !question.trim()
              ? { ...styles.sendButton, ...styles.sendButtonDisabled }
              : styles.sendButton
          }
        >
          {isAsking ? '⏳' : '➤'}
        </button>
      </form>
    </div>
  );
};

const styles = {
  container: {
    padding: '1rem',
    display: 'flex',
    flexDirection: 'column' as const,
    height: '600px',
  },
  emptyState: {
    textAlign: 'center' as const,
    padding: '3rem',
    color: '#666',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  title: {
    margin: '0',
    fontSize: '1.3rem',
    color: '#232f3e',
  },
  clearButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.875rem',
  },
  chatContainer: {
    flex: 1,
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column' as const,
  },
  placeholder: {
    padding: '3rem',
    textAlign: 'center' as const,
    color: '#666',
  },
  suggestions: {
    marginTop: '2rem',
    textAlign: 'left' as const,
    maxWidth: '400px',
    margin: '2rem auto 0',
  },
  messages: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '1.5rem',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '1rem',
  },
  message: {
    padding: '1rem',
    borderRadius: '8px',
    maxWidth: '80%',
  },
  userMessage: {
    backgroundColor: '#e3f2fd',
    alignSelf: 'flex-end',
    marginLeft: 'auto',
  },
  assistantMessage: {
    backgroundColor: '#f5f5f5',
    alignSelf: 'flex-start',
  },
  messageRole: {
    fontWeight: '600',
    marginBottom: '0.5rem',
    fontSize: '0.875rem',
  },
  messageText: {
    margin: '0',
    lineHeight: '1.6',
    whiteSpace: 'pre-wrap' as const,
  },
  linksContainer: {
    marginTop: '1rem',
    padding: '0.75rem',
    backgroundColor: 'rgba(255, 153, 0, 0.1)',
    borderRadius: '4px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.5rem',
  },
  linkButton: {
    display: 'inline-block',
    padding: '0.5rem 1rem',
    backgroundColor: '#ff9900',
    color: 'white',
    textDecoration: 'none',
    borderRadius: '4px',
    fontSize: '0.875rem',
    fontWeight: '600',
    textAlign: 'center' as const,
  },
  inputForm: {
    display: 'flex',
    gap: '0.5rem',
    marginTop: '1rem',
  },
  input: {
    flex: 1,
    padding: '0.75rem',
    border: '2px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
    outline: 'none',
  },
  sendButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#ff9900',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1.2rem',
  },
  sendButtonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
};

export default ChatTab;
