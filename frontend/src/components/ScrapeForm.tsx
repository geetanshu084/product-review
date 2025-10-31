/**
 * Product scraping form component
 */

import React, { useState } from 'react';
import { apiClient } from '@/services/api';
import { useProduct } from '@/contexts/ProductContext';

const ScrapeForm: React.FC = () => {
  const [url, setUrl] = useState<string>('');
  const { setProductData, setAnalysis, setError, setIsLoading, sessionId } = useProduct();

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!url.trim()) {
      setError('Please enter a valid Amazon URL');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Use unified endpoint: scrape-and-analyze
      // This will: scrape → search competitors → search reviews → structure → analyze
      const response = await apiClient.scrapeAndAnalyze({ url, session_id: sessionId });

      if (response.success) {
        // Set both product data and analysis
        if (response.product_data) {
          setProductData(response.product_data);
        }
        if (response.analysis) {
          setAnalysis(response.analysis);
        }
        setError(null);
      } else {
        setError(response.message || 'Failed to analyze product');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze product. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <form onSubmit={handleAnalyze} style={styles.form}>
        <div style={styles.inputGroup}>
          <input
            type="text"
            placeholder="Enter Amazon product URL (e.g., https://amazon.in/dp/B0ABC123)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            style={styles.input}
          />
          <button type="submit" style={styles.button}>
            🚀 Analyze Product
          </button>
        </div>
        <div style={styles.hint}>
          Single click to: Scrape → Search Competitors → Search Reviews → AI Analysis
        </div>
      </form>
    </div>
  );
};

const styles = {
  container: {
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    marginBottom: '1.5rem',
  },
  form: {
    width: '100%',
  },
  inputGroup: {
    display: 'flex',
    gap: '1rem',
    marginBottom: '0.75rem',
  },
  input: {
    flex: 1,
    padding: '0.75rem',
    fontSize: '1rem',
    border: '2px solid #ddd',
    borderRadius: '4px',
    outline: 'none',
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
  hint: {
    fontSize: '0.875rem',
    color: '#666',
    textAlign: 'center' as const,
    fontStyle: 'italic' as const,
  },
};

export default ScrapeForm;
