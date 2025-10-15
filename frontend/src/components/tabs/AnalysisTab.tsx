/**
 * Analysis tab component
 */

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { apiClient } from '@/services/api';
import { useProduct } from '@/contexts/ProductContext';

const AnalysisTab: React.FC = () => {
  const { productData, analysis, setAnalysis, setError, setProductData } = useProduct();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [includePriceComparison, setIncludePriceComparison] = useState(true);
  const [includeWebSearch, setIncludeWebSearch] = useState(true);

  const handleAnalyze = async () => {
    if (!productData?.asin) {
      setError('Please scrape a product first');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await apiClient.analyzeProduct({
        asin: productData.asin,
        include_price_comparison: includePriceComparison,
        include_web_search: includeWebSearch,
      });

      if (response.success) {
        setAnalysis(response.analysis);
        if (response.product_data) {
          setProductData(response.product_data);
        }
      } else {
        setError(response.message || 'Failed to analyze product');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze product. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (!productData) {
    return (
      <div style={styles.emptyState}>
        <p>Please scrape a product first to view analysis.</p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.controls}>
        <h3 style={styles.title}>AI-Powered Analysis</h3>
        <div style={styles.options}>
          <label style={styles.checkbox}>
            <input
              type="checkbox"
              checked={includePriceComparison}
              onChange={(e) => setIncludePriceComparison(e.target.checked)}
            />
            <span>Include Price Comparison</span>
          </label>
          <label style={styles.checkbox}>
            <input
              type="checkbox"
              checked={includeWebSearch}
              onChange={(e) => setIncludeWebSearch(e.target.checked)}
            />
            <span>Include External Reviews</span>
          </label>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={isAnalyzing}
          style={isAnalyzing ? { ...styles.button, ...styles.buttonDisabled } : styles.button}
        >
          {isAnalyzing ? '🔄 Analyzing...' : '🤖 Analyze Product'}
        </button>
      </div>

      {analysis && (
        <div style={styles.analysisContent}>
          <ReactMarkdown>{analysis}</ReactMarkdown>
        </div>
      )}

      {!analysis && !isAnalyzing && (
        <div style={styles.placeholder}>
          <p>Click "Analyze Product" to get AI-powered insights about this product.</p>
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    padding: '1rem',
  },
  emptyState: {
    textAlign: 'center' as const,
    padding: '3rem',
    color: '#666',
  },
  controls: {
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    marginBottom: '1.5rem',
  },
  title: {
    margin: '0 0 1rem',
    fontSize: '1.3rem',
    color: '#232f3e',
  },
  options: {
    display: 'flex',
    gap: '1.5rem',
    marginBottom: '1rem',
  },
  checkbox: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    cursor: 'pointer',
  },
  button: {
    padding: '0.75rem 1.5rem',
    fontSize: '1rem',
    backgroundColor: '#ff9900',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: '600',
  },
  buttonDisabled: {
    opacity: 0.6,
    cursor: 'not-allowed',
  },
  analysisContent: {
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    lineHeight: '1.6',
  },
  placeholder: {
    backgroundColor: 'white',
    padding: '3rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    textAlign: 'center' as const,
    color: '#666',
  },
};

export default AnalysisTab;
