/**
 * Unified Product Analysis View
 * Shows pricing, key highlights, and full analysis in one integrated view
 */

import React from 'react';
import type { ProductData } from '@/types';
import ReactMarkdown from 'react-markdown';

interface ProductAnalysisViewProps {
  product: ProductData;
  analysis: string;
}

const ProductAnalysisView: React.FC<ProductAnalysisViewProps> = ({ product, analysis }) => {
  // Extract numeric price for comparison
  const extractPrice = (priceStr?: string): number => {
    if (!priceStr) return 0;
    const match = priceStr.match(/[\d,]+\.?\d*/);
    if (!match) return 0;
    return parseFloat(match[0].replace(/,/g, ''));
  };

  const basePrice = extractPrice(product.price);

  // Get bank offers
  const bankOffers = product.bank_offers || [];
  const exchangeOffers = bankOffers.filter(offer =>
    offer.offer_type.toLowerCase().includes('exchange')
  );
  const otherOffers = bankOffers.filter(offer =>
    !offer.offer_type.toLowerCase().includes('exchange')
  );

  // Get competitor prices - check multiple possible locations and filter out Amazon
  const allCompetitorPrices = (product as any).competitor_prices ||
                              product.price_comparison?.alternative_prices ||
                              [];
  const competitorPrices = allCompetitorPrices.filter((comp: any) =>
    !comp.site.toLowerCase().includes('amazon')
  );

  // Get key highlights from structured data
  const pros = (product as any).pros || [];
  const cons = (product as any).cons || [];

  return (
    <div style={styles.container}>
      {/* Top Section: Product Header */}
      <div style={styles.header}>
        <div style={styles.headerContent}>
          <div style={styles.titleSection}>
            <h1 style={styles.productTitle}>{product.title}</h1>
            {product.brand && <div style={styles.brand}>by {product.brand}</div>}
          </div>
          <div style={styles.ratingSection}>
            {product.rating && (
              <div style={styles.rating}>
                <span style={styles.ratingValue}>{product.rating}</span>
                <span style={styles.ratingStars}>⭐</span>
              </div>
            )}
            {product.ratings_count && (
              <div style={styles.reviewCount}>{product.ratings_count} ratings</div>
            )}
          </div>
        </div>
      </div>

      {/* Pricing Section */}
      <div style={styles.pricingSection}>
        <h2 style={styles.sectionTitle}>💰 Pricing Overview</h2>

        <div style={styles.priceGrid}>
          {/* Amazon Price without offers */}
          <div style={styles.priceCard}>
            <div style={styles.priceLabel}>Amazon Price</div>
            <div style={styles.priceValue}>{product.price || 'N/A'}</div>
            <div style={styles.priceSubtext}>Without offers</div>
          </div>

          {/* With Bank Offers */}
          {otherOffers.length > 0 && (
            <div style={{...styles.priceCard, ...styles.priceCardHighlight}}>
              <div style={styles.priceLabel}>💳 With Bank Offers</div>
              <div style={styles.priceValue}>{product.price || 'N/A'}</div>
              <div style={styles.priceSubtext}>
                {otherOffers.length} offer{otherOffers.length > 1 ? 's' : ''} available
              </div>
              <div style={styles.offersList}>
                {otherOffers.slice(0, 2).map((offer, idx) => (
                  <div key={idx} style={styles.offerBadge}>
                    {offer.bank}: {offer.offer_type}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Competitor Prices */}
          {competitorPrices.length > 0 && (
            <div style={styles.priceCard}>
              <div style={styles.priceLabel}>🔍 Competitor Prices</div>
              <div style={styles.competitorList}>
                {competitorPrices.map((competitor, idx) => (
                  <div key={idx} style={styles.competitorItem}>
                    <div style={styles.competitorSite}>{competitor.site}</div>
                    <div style={styles.competitorPrice}>{competitor.price}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* All Bank Offers */}
        {bankOffers.length > 0 && (
          <div style={styles.allOffersSection}>
            <h3 style={styles.subsectionTitle}>Available Offers</h3>
            <div style={styles.offersGrid}>
              {bankOffers.map((offer, idx) => (
                <div key={idx} style={styles.offerCard}>
                  <div style={styles.offerHeader}>
                    <span style={styles.offerBank}>{offer.bank}</span>
                    <span style={styles.offerType}>{offer.offer_type}</span>
                  </div>
                  <div style={styles.offerDescription}>{offer.description}</div>
                  {offer.terms && (
                    <div style={styles.offerTerms}>T&C: {offer.terms}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Key Highlights Section */}
      <div style={styles.highlightsSection}>
        <h2 style={styles.sectionTitle}>✨ Key Highlights</h2>

        <div style={styles.highlightsGrid}>
          {/* Product Info */}
          <div style={styles.highlightCard}>
            <h3 style={styles.highlightTitle}>📦 Product Info</h3>
            <div style={styles.infoList}>
              <div style={styles.infoItem}>
                <span style={styles.infoLabel}>ASIN:</span>
                <span style={styles.infoValue}>{product.asin}</span>
              </div>
              {product.brand && (
                <div style={styles.infoItem}>
                  <span style={styles.infoLabel}>Brand:</span>
                  <span style={styles.infoValue}>{product.brand}</span>
                </div>
              )}
              {product.rating && (
                <div style={styles.infoItem}>
                  <span style={styles.infoLabel}>Rating:</span>
                  <span style={styles.infoValue}>{product.rating} ⭐</span>
                </div>
              )}
            </div>
          </div>

          {/* Pros */}
          {pros.length > 0 && (
            <div style={styles.highlightCard}>
              <h3 style={styles.highlightTitle}>✅ Top Pros</h3>
              <ul style={styles.highlightList}>
                {pros.slice(0, 5).map((pro: string, idx: number) => (
                  <li key={idx} style={styles.highlightListItem}>{pro}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Cons */}
          {cons.length > 0 && (
            <div style={styles.highlightCard}>
              <h3 style={styles.highlightTitle}>⚠️ Top Cons</h3>
              <ul style={styles.highlightList}>
                {cons.slice(0, 5).map((con: string, idx: number) => (
                  <li key={idx} style={styles.highlightListItem}>{con}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Full Analysis Section */}
      <div style={styles.analysisSection}>
        <h2 style={styles.sectionTitle}>📊 Complete Analysis</h2>
        <div style={styles.analysisContent}>
          <ReactMarkdown>{analysis}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    overflow: 'hidden',
  },

  // Header
  header: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    padding: '2rem',
  },
  headerContent: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: '2rem',
    flexWrap: 'wrap' as const,
  },
  titleSection: {
    flex: 1,
    minWidth: '300px',
  },
  productTitle: {
    fontSize: '1.75rem',
    fontWeight: 'bold' as const,
    margin: '0 0 0.5rem 0',
    lineHeight: 1.3,
  },
  brand: {
    fontSize: '1rem',
    opacity: 0.9,
  },
  ratingSection: {
    textAlign: 'right' as const,
  },
  rating: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    justifyContent: 'flex-end',
  },
  ratingValue: {
    fontSize: '2rem',
    fontWeight: 'bold' as const,
  },
  ratingStars: {
    fontSize: '1.5rem',
  },
  reviewCount: {
    fontSize: '0.875rem',
    opacity: 0.9,
    marginTop: '0.25rem',
  },

  // Pricing Section
  pricingSection: {
    padding: '2rem',
    backgroundColor: '#f8f9fa',
    borderBottom: '1px solid #e0e0e0',
  },
  sectionTitle: {
    fontSize: '1.5rem',
    fontWeight: 'bold' as const,
    marginBottom: '1.5rem',
    color: '#2c3e50',
  },
  priceGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '1rem',
    marginBottom: '2rem',
  },
  priceCard: {
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    border: '2px solid #e0e0e0',
    textAlign: 'center' as const,
  },
  priceCardHighlight: {
    borderColor: '#4CAF50',
    backgroundColor: '#f1f8f4',
  },
  priceLabel: {
    fontSize: '0.875rem',
    color: '#666',
    fontWeight: '600' as const,
    marginBottom: '0.5rem',
    textTransform: 'uppercase' as const,
  },
  priceValue: {
    fontSize: '2rem',
    fontWeight: 'bold' as const,
    color: '#2c3e50',
    margin: '0.5rem 0',
  },
  priceSubtext: {
    fontSize: '0.875rem',
    color: '#888',
  },
  offersList: {
    marginTop: '1rem',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.5rem',
  },
  offerBadge: {
    fontSize: '0.75rem',
    padding: '0.5rem',
    backgroundColor: '#e3f2fd',
    color: '#1976d2',
    borderRadius: '4px',
    fontWeight: '500' as const,
  },
  moreCompetitors: {
    fontSize: '0.75rem',
    color: '#1976d2',
    marginTop: '0.5rem',
    fontStyle: 'italic' as const,
  },
  competitorList: {
    marginTop: '1rem',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.75rem',
  },
  competitorItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.5rem 0',
    borderBottom: '1px solid #e0e0e0',
  },
  competitorSite: {
    fontSize: '0.875rem',
    fontWeight: '500' as const,
    color: '#555',
  },
  competitorPrice: {
    fontSize: '1.125rem',
    fontWeight: 'bold' as const,
    color: '#2c3e50',
  },

  // All Offers
  allOffersSection: {
    marginTop: '2rem',
    paddingTop: '2rem',
    borderTop: '2px solid #e0e0e0',
  },
  subsectionTitle: {
    fontSize: '1.25rem',
    fontWeight: 'bold' as const,
    marginBottom: '1rem',
    color: '#2c3e50',
  },
  offersGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '1rem',
  },
  offerCard: {
    backgroundColor: 'white',
    padding: '1rem',
    borderRadius: '6px',
    border: '1px solid #e0e0e0',
  },
  offerHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  offerBank: {
    fontWeight: 'bold' as const,
    color: '#1976d2',
  },
  offerType: {
    fontSize: '0.75rem',
    padding: '0.25rem 0.5rem',
    backgroundColor: '#e3f2fd',
    color: '#1976d2',
    borderRadius: '4px',
  },
  offerDescription: {
    fontSize: '0.875rem',
    color: '#555',
    marginBottom: '0.5rem',
  },
  offerTerms: {
    fontSize: '0.75rem',
    color: '#888',
    fontStyle: 'italic' as const,
  },

  // Highlights Section
  highlightsSection: {
    padding: '2rem',
    backgroundColor: 'white',
    borderBottom: '1px solid #e0e0e0',
  },
  highlightsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '1.5rem',
  },
  highlightCard: {
    backgroundColor: '#f8f9fa',
    padding: '1.5rem',
    borderRadius: '8px',
    border: '1px solid #e0e0e0',
  },
  highlightTitle: {
    fontSize: '1.125rem',
    fontWeight: 'bold' as const,
    marginBottom: '1rem',
    color: '#2c3e50',
  },
  infoList: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.75rem',
  },
  infoItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  infoLabel: {
    fontWeight: '600' as const,
    color: '#666',
  },
  infoValue: {
    color: '#2c3e50',
  },
  highlightList: {
    margin: 0,
    paddingLeft: '1.25rem',
    listStyle: 'disc',
  },
  highlightListItem: {
    marginBottom: '0.5rem',
    color: '#555',
    lineHeight: 1.5,
  },

  // Analysis Section
  analysisSection: {
    padding: '2rem',
    backgroundColor: 'white',
  },
  analysisContent: {
    fontSize: '1rem',
    lineHeight: 1.8,
    color: '#333',
  },
};

export default ProductAnalysisView;
