/**
 * Main App component
 */

import React, { useState } from 'react';
import { ProductProvider, useProduct } from './contexts/ProductContext';
import Header from './components/Header';
import ProductAnalysisView from './components/ProductAnalysisView';
import ReviewsTab from './components/tabs/ReviewsTab';
import ChatTab from './components/tabs/ChatTab';

const AppContent: React.FC = () => {
  const { productData, analysis, isLoading, error } = useProduct();
  const [leftView, setLeftView] = useState<'analysis' | 'platform' | 'external' | 'summary'>('analysis');

  return (
    <>
      <style>{`
        /* Custom scrollbar styling */
        .scrollable-content {
          scrollbar-width: thin;
          scrollbar-color: transparent transparent;
          transition: scrollbar-color 0.3s ease;
        }

        .scrollable-content:hover {
          scrollbar-color: rgba(0, 0, 0, 0.3) transparent;
        }

        .scrollable-content::-webkit-scrollbar {
          width: 8px;
        }

        .scrollable-content::-webkit-scrollbar-track {
          background: transparent;
        }

        .scrollable-content::-webkit-scrollbar-thumb {
          background: transparent;
          border-radius: 4px;
          transition: background 0.3s ease;
        }

        .scrollable-content:hover::-webkit-scrollbar-thumb {
          background: rgba(0, 0, 0, 0.3);
        }

        .scrollable-content::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 0, 0, 0.5);
        }

        @media (max-width: 1024px) {
          .two-column-layout {
            grid-template-columns: 1fr !important;
          }
          .sticky-chat {
            position: relative !important;
            height: 600px !important;
            max-height: 600px !important;
          }
        }
        @media (max-width: 768px) {
          .header-container {
            flex-direction: column !important;
            align-items: stretch !important;
            gap: 1rem !important;
          }
        }
      `}</style>
      <div style={styles.app}>
        <Header />

        <main style={styles.main}>
        <div style={styles.container}>

          {error && (
            <div style={styles.errorBanner}>
              <strong>❌ Error:</strong> {error}
            </div>
          )}

          {isLoading && (
            <div style={styles.loadingBanner}>
              <div style={styles.spinner}>⏳</div>
              <span>Analyzing product... This may take 30-60 seconds</span>
            </div>
          )}

          {productData && analysis && (
            <div className="two-column-layout" style={styles.twoColumnLayout}>
              {/* Left Column - Analysis & Reviews */}
              <div style={styles.leftColumn}>
                {/* Sub-navigation for left column */}
                <div style={styles.leftNav}>
                  <button
                    onClick={() => setLeftView('analysis')}
                    style={
                      leftView === 'analysis'
                        ? { ...styles.navButton, ...styles.navButtonActive }
                        : styles.navButton
                    }
                  >
                    📊 Analysis
                  </button>
                  <button
                    onClick={() => setLeftView('platform')}
                    style={
                      leftView === 'platform'
                        ? { ...styles.navButton, ...styles.navButtonActive }
                        : styles.navButton
                    }
                  >
                    ⭐ Reviews ({productData.reviews?.length || 0})
                  </button>
                  <button
                    onClick={() => setLeftView('external')}
                    style={
                      leftView === 'external'
                        ? { ...styles.navButton, ...styles.navButtonActive }
                        : styles.navButton
                    }
                  >
                    🌐 External
                  </button>
                  <button
                    onClick={() => setLeftView('summary')}
                    style={
                      leftView === 'summary'
                        ? { ...styles.navButton, ...styles.navButtonActive }
                        : styles.navButton
                    }
                  >
                    📊 Summary
                  </button>
                </div>

                {/* Left column content */}
                <div className="scrollable-content" style={styles.leftContent}>
                  {leftView === 'analysis' && (
                    <ProductAnalysisView product={productData} analysis={analysis} />
                  )}
                  {(leftView === 'platform' || leftView === 'external' || leftView === 'summary') && (
                    <ReviewsTab activeView={leftView} />
                  )}
                </div>
              </div>

              {/* Right Column - Chat (Sticky) */}
              <div style={styles.rightColumn}>
                <div className="sticky-chat" style={styles.stickyChat}>
                  <ChatTab />
                </div>
              </div>
            </div>
          )}

          {!productData && !isLoading && !error && (
            <div style={styles.welcomeMessage}>
              <h2>👋 Welcome to Amazon Product Analysis Agent</h2>
              <p>
                Get AI-powered insights about any Amazon product. Simply paste a product URL
                above to get started!
              </p>
              <div style={styles.features}>
                <div style={styles.feature}>
                  <div style={styles.featureIcon}>📊</div>
                  <h3>Smart Analysis</h3>
                  <p>AI-powered product analysis with pros, cons, and recommendations</p>
                </div>
                <div style={styles.feature}>
                  <div style={styles.featureIcon}>⭐</div>
                  <h3>Review Insights</h3>
                  <p>Aggregated reviews from Amazon and external sources</p>
                </div>
                <div style={styles.feature}>
                  <div style={styles.featureIcon}>💬</div>
                  <h3>Interactive Q&A</h3>
                  <p>Ask questions and get instant answers about the product</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

        <footer style={styles.footer}>
          <p>Powered by geetanshu.ai 🚀</p>
        </footer>
    </div>
    </>
  );
};

const App: React.FC = () => {
  return (
    <ProductProvider>
      <AppContent />
    </ProductProvider>
  );
};

const styles = {
  app: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    display: 'flex',
    flexDirection: 'column' as const,
    overflowX: 'hidden' as const,
    width: '100%',
    height: '100vh',
    overflow: 'hidden',
  },
  main: {
    flex: 1,
    padding: '0.5rem 0 0 0',
    width: '100%',
    overflowX: 'hidden' as const,
    overflowY: 'hidden' as const,
    display: 'flex',
    flexDirection: 'column' as const,
    minHeight: 0,
  },
  container: {
    maxWidth: '100%',
    width: '100%',
    flex: 1,
    margin: '0 auto',
    padding: '0 1rem 0.5rem 1rem',
    boxSizing: 'border-box' as const,
    display: 'flex',
    flexDirection: 'column' as const,
    minHeight: 0,
  },
  errorBanner: {
    backgroundColor: '#ffebee',
    color: '#c62828',
    padding: '1rem',
    borderRadius: '4px',
    marginBottom: '1rem',
    border: '1px solid #ef9a9a',
  },
  loadingBanner: {
    backgroundColor: '#fff3cd',
    color: '#856404',
    padding: '1rem',
    borderRadius: '4px',
    marginBottom: '1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    border: '1px solid #ffeaa7',
  },
  spinner: {
    animation: 'spin 1s linear infinite',
  },
  twoColumnLayout: {
    display: 'grid',
    gridTemplateColumns: '7fr 3fr',
    gap: '1rem',
    alignItems: 'start',
    width: '100%',
    boxSizing: 'border-box' as const,
    overflow: 'visible' as const,
    flex: 1,
    minHeight: 0,
  },
  leftColumn: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0',
    width: '100%',
    height: '100%',
    minWidth: 0,
    minHeight: 0,
    boxSizing: 'border-box' as const,
    overflow: 'hidden',
  },
  leftNav: {
    display: 'flex',
    gap: '0.25rem',
    marginBottom: '0',
    borderBottom: '2px solid #e0e0e0',
    backgroundColor: 'white',
    borderTopLeftRadius: '8px',
    borderTopRightRadius: '8px',
    padding: '0.5rem 0.5rem 0',
    flexShrink: 0,
    overflowX: 'auto' as const,
  },
  navButton: {
    padding: '0.75rem 1rem',
    backgroundColor: 'transparent',
    border: 'none',
    borderBottom: '3px solid transparent',
    cursor: 'pointer',
    fontSize: '0.9rem',
    color: '#666',
    fontWeight: '500',
    transition: 'all 0.2s',
    whiteSpace: 'nowrap' as const,
  },
  navButtonActive: {
    borderBottomColor: '#ff9900',
    color: '#232f3e',
    fontWeight: '600',
  },
  leftContent: {
    backgroundColor: '#fafafa',
    borderBottomLeftRadius: '8px',
    borderBottomRightRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    flex: 1,
    minHeight: 0,
    overflowY: 'auto' as const,
    overflowX: 'hidden' as const,
  },
  rightColumn: {
    position: 'relative' as const,
    width: '100%',
    height: '100%',
    minWidth: 0,
    minHeight: 0,
    boxSizing: 'border-box' as const,
    overflow: 'hidden',
  },
  stickyChat: {
    position: 'relative' as const,
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
    height: '100%',
    display: 'flex',
    flexDirection: 'column' as const,
    overflow: 'hidden',
    width: '100%',
    minWidth: 0,
    boxSizing: 'border-box' as const,
  },
  welcomeMessage: {
    backgroundColor: 'white',
    padding: '3rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    textAlign: 'center' as const,
  },
  features: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '2rem',
    marginTop: '3rem',
  },
  feature: {
    padding: '1.5rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '8px',
  },
  featureIcon: {
    fontSize: '3rem',
    marginBottom: '1rem',
  },
  footer: {
    backgroundColor: '#232f3e',
    color: 'white',
    textAlign: 'center' as const,
    padding: '0.75rem 0',
    marginTop: '0',
  },
};

export default App;
