/**
 * Header component with integrated form
 */

import React, { useState } from 'react';
import { apiClient } from '@/services/api';
import { useProduct } from '@/contexts/ProductContext';

const Header: React.FC = () => {
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
      const response = await apiClient.scrapeAndAnalyze({ url, session_id: sessionId });

      if (response.success) {
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
    <header style={styles.header}>
      <div className="header-container" style={styles.container}>
        {/* Left: Branding */}
        <div style={styles.branding}>
          <h1 style={styles.title}>🛍️ Product Analysis Agent</h1>
          <p style={styles.subtitle}>AI-powered insights</p>
        </div>

        {/* Right: Form */}
        <form onSubmit={handleAnalyze} style={styles.form}>
          <input
            type="text"
            placeholder="Enter product URL (Amazon/Flipkart)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            style={styles.input}
          />
          <button type="submit" style={styles.button}>
            ➤
          </button>
        </form>
      </div>
    </header>
  );
};

const styles = {
  header: {
    backgroundColor: '#232f3e',
    color: 'white',
    padding: '1rem 0',
    borderBottom: '3px solid #ff9900',
  },
  container: {
    maxWidth: '100%',
    margin: '0 auto',
    padding: '0 1rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '2rem',
  },
  branding: {
    flex: '0 0 auto',
  },
  title: {
    margin: '0',
    fontSize: '1.5rem',
    fontWeight: '600',
  },
  subtitle: {
    margin: '0.25rem 0 0',
    fontSize: '0.875rem',
    opacity: 0.9,
  },
  form: {
    flex: '1 1 auto',
    maxWidth: '600px',
    display: 'flex',
    gap: '0.5rem',
  },
  input: {
    flex: 1,
    padding: '0.625rem 1rem',
    fontSize: '0.95rem',
    border: '2px solid #ddd',
    borderRadius: '4px',
    outline: 'none',
  },
  button: {
    padding: '0.625rem 1.25rem',
    fontSize: '1.2rem',
    backgroundColor: '#ff9900',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: '600',
    transition: 'background-color 0.2s',
  },
};

export default Header;
