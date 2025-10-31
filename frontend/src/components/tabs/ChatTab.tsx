/**
 * Chat/Q&A tab component
 */

import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { apiClient } from '@/services/api';
import { useProduct } from '@/contexts/ProductContext';

const ChatTab: React.FC = () => {
  const { productData, sessionId, chatHistory, addChatMessage, removeTypingIndicator, clearChat } = useProduct();
  const [question, setQuestion] = useState<string>('');
  const [isAsking, setIsAsking] = useState<boolean>(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();

    // Use product_id (preferred) or asin (backward compatibility)
    const productId = productData?.product_id || productData?.asin;

    if (!question.trim() || !productId) {
      return;
    }

    const userQuestion = question.trim();
    setQuestion(''); // Clear input immediately
    setIsAsking(true);

    // Add user message
    addChatMessage({ role: 'user', content: userQuestion });

    // Add typing indicator as a temporary assistant message
    addChatMessage({ role: 'assistant', content: '___TYPING___' });

    try {
      const response = await apiClient.askQuestion({
        session_id: sessionId,
        product_id: productId,
        question: userQuestion,
      });

      // Remove typing indicator before adding response
      removeTypingIndicator();

      if (response.success) {
        addChatMessage({ role: 'assistant', content: response.answer });
      } else {
        addChatMessage({
          role: 'assistant',
          content: 'Sorry, I could not process your question. Please try again.',
        });
      }
    } catch (err: any) {
      // Remove typing indicator before adding error message
      removeTypingIndicator();
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

  // Render markdown message with custom components
  const renderMarkdown = (content: string) => {
    return (
      <ReactMarkdown
        components={{
          // Style paragraphs
          p: ({ children }) => (
            <p style={styles.markdownParagraph}>{children}</p>
          ),
          // Style headings
          h1: ({ children }) => (
            <h1 style={styles.markdownH1}>{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 style={styles.markdownH2}>{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 style={styles.markdownH3}>{children}</h3>
          ),
          // Style links
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              style={styles.markdownLink}
            >
              {children}
            </a>
          ),
          // Style lists
          ul: ({ children }) => (
            <ul style={styles.markdownList}>{children}</ul>
          ),
          ol: ({ children }) => (
            <ol style={styles.markdownList}>{children}</ol>
          ),
          li: ({ children }) => (
            <li style={styles.markdownListItem}>{children}</li>
          ),
          // Style code blocks
          code: ({ inline, children, ...props }: any) => {
            return inline ? (
              <code style={styles.markdownInlineCode}>{children}</code>
            ) : (
              <pre style={styles.markdownCodeBlock}>
                <code>{children}</code>
              </pre>
            );
          },
          // Style blockquotes
          blockquote: ({ children }) => (
            <blockquote style={styles.markdownBlockquote}>{children}</blockquote>
          ),
          // Style strong/bold
          strong: ({ children }) => (
            <strong style={styles.markdownStrong}>{children}</strong>
          ),
          // Style em/italic
          em: ({ children }) => (
            <em style={styles.markdownEm}>{children}</em>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
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
    <>
      <style>{`
        @keyframes typingAnimation {
          0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.7;
          }
          30% {
            transform: translateY(-10px);
            opacity: 1;
          }
        }

        .clear-chat-btn:hover {
          background-color: rgba(220, 53, 69, 0.1);
          transform: scale(1.1);
        }

        .clear-chat-btn:active {
          transform: scale(0.95);
        }
      `}</style>
      <div style={styles.container}>
        <div style={styles.header}>
        <h3 style={styles.title}>💬 Ask Questions About This Product</h3>
        {chatHistory.length > 0 && (
          <button onClick={handleClearChat} className="clear-chat-btn" style={styles.clearButton} title="Clear chat">
            🗑️
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
          <div className="scrollable-content" style={styles.messages}>
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
                {msg.content === '___TYPING___' ? (
                  <div style={styles.typingIndicator}>
                    <span style={{...styles.typingDot, animationDelay: '0s'}}></span>
                    <span style={{...styles.typingDot, animationDelay: '0.2s'}}></span>
                    <span style={{...styles.typingDot, animationDelay: '0.4s'}}></span>
                  </div>
                ) : msg.role === 'assistant' ? (
                  <div style={styles.markdownContainer}>
                    {renderMarkdown(msg.content)}
                  </div>
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
    </>
  );
};

const styles = {
  container: {
    padding: '1rem',
    display: 'flex',
    flexDirection: 'column' as const,
    flex: 1,
    minHeight: 0,
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
    fontSize: '1.1rem',
    color: '#232f3e',
  },
  clearButton: {
    padding: '0.5rem',
    backgroundColor: 'transparent',
    color: '#dc3545',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1.25rem',
    transition: 'background-color 0.2s, transform 0.1s',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  chatContainer: {
    flex: 1,
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    display: 'flex',
    flexDirection: 'column' as const,
    minHeight: 0,
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
    wordBreak: 'break-word' as const,
    overflowWrap: 'break-word' as const,
  },
  markdownContainer: {
    width: '100%',
  },
  markdownParagraph: {
    margin: '0 0 0.75rem 0',
    lineHeight: '1.6',
    color: '#333',
  },
  markdownH1: {
    fontSize: '1.5rem',
    fontWeight: '700',
    margin: '1rem 0 0.75rem 0',
    color: '#232f3e',
  },
  markdownH2: {
    fontSize: '1.3rem',
    fontWeight: '600',
    margin: '0.875rem 0 0.5rem 0',
    color: '#232f3e',
  },
  markdownH3: {
    fontSize: '1.1rem',
    fontWeight: '600',
    margin: '0.75rem 0 0.5rem 0',
    color: '#232f3e',
  },
  markdownLink: {
    color: '#007bff',
    textDecoration: 'none',
    borderBottom: '1px solid #007bff',
    transition: 'color 0.2s, border-color 0.2s',
  },
  markdownList: {
    margin: '0.5rem 0',
    paddingLeft: '1.5rem',
    lineHeight: '1.6',
  },
  markdownListItem: {
    marginBottom: '0.25rem',
  },
  markdownInlineCode: {
    backgroundColor: '#f4f4f4',
    padding: '0.125rem 0.375rem',
    borderRadius: '3px',
    fontFamily: 'monospace',
    fontSize: '0.9em',
    color: '#d63384',
    border: '1px solid #e0e0e0',
  },
  markdownCodeBlock: {
    backgroundColor: '#f8f9fa',
    padding: '1rem',
    borderRadius: '4px',
    overflow: 'auto',
    margin: '0.75rem 0',
    border: '1px solid #e0e0e0',
    fontFamily: 'monospace',
    fontSize: '0.875rem',
    lineHeight: '1.5',
  },
  markdownBlockquote: {
    margin: '0.75rem 0',
    padding: '0.5rem 1rem',
    borderLeft: '4px solid #ff9900',
    backgroundColor: '#f8f9fa',
    fontStyle: 'italic',
    color: '#666',
  },
  markdownStrong: {
    fontWeight: '600',
    color: '#232f3e',
  },
  markdownEm: {
    fontStyle: 'italic',
    color: '#555',
  },
  inputForm: {
    display: 'flex',
    gap: '0.5rem',
    marginTop: '1rem',
    flexShrink: 0,
    padding: '0.5rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
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
  typingIndicator: {
    display: 'flex',
    gap: '0.3rem',
    alignItems: 'center',
    padding: '0.5rem 0',
  },
  typingDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: '#666',
    display: 'inline-block',
    animation: 'typingAnimation 1.4s infinite ease-in-out',
  } as React.CSSProperties & { animation: string },
};

export default ChatTab;
