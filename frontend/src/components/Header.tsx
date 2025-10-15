/**
 * Header component
 */

import React from 'react';

const Header: React.FC = () => {
  return (
    <header style={styles.header}>
      <div style={styles.container}>
        <h1 style={styles.title}>🛍️ Amazon Product Analysis Agent</h1>
        <p style={styles.subtitle}>Analyze products with AI-powered insights</p>
      </div>
    </header>
  );
};

const styles = {
  header: {
    backgroundColor: '#232f3e',
    color: 'white',
    padding: '1.5rem 0',
    borderBottom: '3px solid #ff9900',
  },
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '0 1rem',
  },
  title: {
    margin: '0',
    fontSize: '2rem',
    fontWeight: '600',
  },
  subtitle: {
    margin: '0.5rem 0 0',
    fontSize: '1rem',
    opacity: 0.9,
  },
};

export default Header;
