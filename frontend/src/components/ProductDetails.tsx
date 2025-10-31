/**
 * Product details component
 */

import React from 'react';
import type { ProductData } from '@/types';
import PriceOverview from './PriceOverview';

interface ProductDetailsProps {
  product: ProductData;
}

const ProductDetails: React.FC<ProductDetailsProps> = ({ product }) => {
  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>{product.title}</h2>
        {product.brand && <p style={styles.brand}>Brand: {product.brand}</p>}
      </div>

      {/* Price Overview Section */}
      <PriceOverview product={product} />

      <div style={styles.info}>
        <div style={styles.infoItem}>
          <strong>ASIN:</strong> {product.asin}
        </div>
        {product.price && (
          <div style={styles.infoItem}>
            <strong>Price:</strong> {product.price}
          </div>
        )}
        {product.rating && (
          <div style={styles.infoItem}>
            <strong>Rating:</strong> {product.rating} ⭐
          </div>
        )}
        {product.ratings_count && (
          <div style={styles.infoItem}>
            <strong>Reviews:</strong> {product.ratings_count}
          </div>
        )}
      </div>

      {product.features && product.features.length > 0 && (
        <div style={styles.section}>
          <h3 style={styles.sectionTitle}>Key Features</h3>
          <ul style={styles.list}>
            {product.features.map((feature, idx) => (
              <li key={idx} style={styles.listItem}>{feature}</li>
            ))}
          </ul>
        </div>
      )}

      {product.description && (
        <div style={styles.section}>
          <h3 style={styles.sectionTitle}>Description</h3>
          <p style={styles.description}>{product.description}</p>
        </div>
      )}
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
  header: {
    borderBottom: '2px solid #f0f0f0',
    paddingBottom: '1rem',
    marginBottom: '1rem',
  },
  title: {
    margin: '0 0 0.5rem',
    fontSize: '1.5rem',
    color: '#232f3e',
  },
  brand: {
    margin: '0',
    fontSize: '1rem',
    color: '#666',
  },
  info: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
    marginBottom: '1.5rem',
  },
  infoItem: {
    padding: '0.75rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
  },
  section: {
    marginTop: '1.5rem',
  },
  sectionTitle: {
    fontSize: '1.2rem',
    color: '#232f3e',
    marginBottom: '0.75rem',
  },
  list: {
    margin: '0',
    paddingLeft: '1.5rem',
  },
  listItem: {
    marginBottom: '0.5rem',
    lineHeight: '1.6',
  },
  description: {
    lineHeight: '1.6',
    color: '#333',
  },
};

export default ProductDetails;
