/**
 * Main App component
 */

import React, { useState } from 'react';
import { ProductProvider, useProduct } from './contexts/ProductContext';
import Header from './components/Header';
import ScrapeForm from './components/ScrapeForm';
import ProductAnalysisView from './components/ProductAnalysisView';
import ReviewsTab from './components/tabs/ReviewsTab';
import ChatTab from './components/tabs/ChatTab';

const AppContent: React.FC = () => {
  const { productData, analysis, isLoading, error } = useProduct();
  const [activeTab, setActiveTab] = useState<'analysis' | 'reviews' | 'chat'>('analysis');

  return (
    <div style={styles.app}>
      <Header />

      <main style={styles.main}>
        <div style={styles.container}>
          <ScrapeForm />

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
            <>
              {/* Tabs */}
              <div style={styles.tabs}>
                <button
                  onClick={() => setActiveTab('analysis')}
                  style={
                    activeTab === 'analysis'
                      ? { ...styles.tab, ...styles.tabActive }
                      : styles.tab
                  }
                >
                  📊 Analysis
                </button>
                <button
                  onClick={() => setActiveTab('reviews')}
                  style={
                    activeTab === 'reviews'
                      ? { ...styles.tab, ...styles.tabActive }
                      : styles.tab
                  }
                >
                  ⭐ Reviews ({productData.reviews?.length || 0})
                </button>
                <button
                  onClick={() => setActiveTab('chat')}
                  style={
                    activeTab === 'chat'
                      ? { ...styles.tab, ...styles.tabActive }
                      : styles.tab
                  }
                >
                  💬 Q&A
                </button>
              </div>

              {/* Tab Content */}
              <div style={styles.tabContent}>
                {activeTab === 'analysis' && (
                  <ProductAnalysisView product={productData} analysis={analysis} />
                )}
                {activeTab === 'reviews' && <ReviewsTab />}
                {activeTab === 'chat' && <ChatTab />}
              </div>
            </>
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
        <p>Powered by FastAPI, LangChain, and Google Gemini 🚀</p>
      </footer>
    </div>
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
  },
  main: {
    flex: 1,
    padding: '2rem 0',
  },
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '0 1rem',
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
  tabs: {
    display: 'flex',
    gap: '0.5rem',
    marginBottom: '0',
    borderBottom: '2px solid #e0e0e0',
    backgroundColor: 'white',
    borderTopLeftRadius: '8px',
    borderTopRightRadius: '8px',
    padding: '0.5rem 0.5rem 0',
  },
  tab: {
    padding: '0.75rem 2rem',
    backgroundColor: 'transparent',
    border: 'none',
    borderBottom: '3px solid transparent',
    cursor: 'pointer',
    fontSize: '1rem',
    color: '#666',
    fontWeight: '500',
  },
  tabActive: {
    borderBottomColor: '#ff9900',
    color: '#232f3e',
    fontWeight: '600',
  },
  tabContent: {
    backgroundColor: '#fafafa',
    borderBottomLeftRadius: '8px',
    borderBottomRightRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    minHeight: '400px',
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
    padding: '1.5rem 0',
    marginTop: '3rem',
  },
};

export default App;
