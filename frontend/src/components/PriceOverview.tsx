/**
 * Price Overview Component
 * Displays pricing information at the top of product details
 */

import React from 'react';
import type { ProductData } from '@/types';

interface PriceOverviewProps {
  product: ProductData;
}

const PriceOverview: React.FC<PriceOverviewProps> = ({ product }) => {
  // Extract base price (remove currency symbol and commas for comparison)
  const extractPrice = (priceStr?: string): number => {
    if (!priceStr) return 0;
    const match = priceStr.match(/[\d,]+\.?\d*/);
    if (!match) return 0;
    return parseFloat(match[0].replace(/,/g, ''));
  };

  const basePrice = extractPrice(product.price);

  // Find minimum price with bank offers
  const exchangeOffers = product.bank_offers?.filter(offer =>
    offer.offer_type.toLowerCase().includes('exchange')
  ) || [];

  const otherOffers = product.bank_offers?.filter(offer =>
    !offer.offer_type.toLowerCase().includes('exchange')
  ) || [];

  // Get best exchange offer (assuming it has price info in description)
  const bestExchangeOffer = exchangeOffers.length > 0 ? exchangeOffers[0] : null;

  // Get top 2 competitor prices
  const competitorPrices = product.price_comparison?.alternative_prices?.slice(0, 2) || [];

  return (
    <div style={styles.container}>
      <div style={styles.priceGrid}>
        {/* Amazon Base Price */}
        <div style={styles.priceCard}>
          <div style={styles.cardLabel}>Amazon Price</div>
          <div style={styles.cardPrice}>{product.price || 'N/A'}</div>
          <div style={styles.cardSubtext}>Without offers</div>
        </div>

        {/* Minimum Price with Bank Offers */}
        {otherOffers.length > 0 && (
          <div style={styles.priceCard}>
            <div style={styles.cardLabel}>💳 With Bank Offers</div>
            <div style={styles.cardPrice}>{product.price || 'N/A'}</div>
            <div style={styles.cardSubtext}>
              {otherOffers.length} offer{otherOffers.length > 1 ? 's' : ''} available
            </div>
            <div style={styles.offersList}>
              {otherOffers.slice(0, 2).map((offer, idx) => (
                <div key={idx} style={styles.offerItem}>
                  <span style={styles.offerBank}>{offer.bank}</span>: {offer.description}
                </div>
              ))}
              {otherOffers.length > 2 && (
                <div style={styles.moreOffers}>+{otherOffers.length - 2} more offers</div>
              )}
            </div>
          </div>
        )}

        {/* Exchange Benefit */}
        {bestExchangeOffer && (
          <div style={styles.priceCard}>
            <div style={styles.cardLabel}>🔄 Exchange Benefits</div>
            <div style={styles.cardPrice}>Check Offer</div>
            <div style={styles.cardSubtext}>{bestExchangeOffer.bank}</div>
            <div style={styles.offersList}>
              <div style={styles.offerItem}>{bestExchangeOffer.description}</div>
            </div>
          </div>
        )}

        {/* Competitor Prices */}
        {competitorPrices.length > 0 && (
          <div style={styles.priceCard}>
            <div style={styles.cardLabel}>🔍 Competitor Prices</div>
            {competitorPrices.map((competitor, idx) => (
              <div key={idx} style={styles.competitorItem}>
                <div style={styles.competitorName}>{competitor.site}</div>
                <div style={styles.competitorPrice}>{competitor.price}</div>
                <div style={styles.competitorAvailability}>{competitor.availability}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* All Bank Offers Section */}
      {product.bank_offers && product.bank_offers.length > 0 && (
        <div style={styles.allOffersSection}>
          <h4 style={styles.allOffersTitle}>💰 All Available Offers ({product.bank_offers.length})</h4>
          <div style={styles.allOffersGrid}>
            {product.bank_offers.map((offer, idx) => (
              <div key={idx} style={styles.offerCard}>
                <div style={styles.offerCardHeader}>
                  <span style={styles.offerCardBank}>{offer.bank}</span>
                  <span style={styles.offerCardType}>{offer.offer_type}</span>
                </div>
                <div style={styles.offerCardDescription}>{offer.description}</div>
                {offer.terms && (
                  <div style={styles.offerCardTerms}>T&C: {offer.terms}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    backgroundColor: '#f8f9fa',
    padding: '1.5rem',
    borderRadius: '8px',
    marginBottom: '1.5rem',
    border: '2px solid #e9ecef',
  },
  priceGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '1rem',
    marginBottom: '1.5rem',
  },
  priceCard: {
    backgroundColor: 'white',
    padding: '1rem',
    borderRadius: '6px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    border: '1px solid #dee2e6',
  },
  cardLabel: {
    fontSize: '0.875rem',
    fontWeight: 'bold' as const,
    color: '#6c757d',
    marginBottom: '0.5rem',
  },
  cardPrice: {
    fontSize: '1.5rem',
    fontWeight: 'bold' as const,
    color: '#28a745',
    marginBottom: '0.25rem',
  },
  cardSubtext: {
    fontSize: '0.75rem',
    color: '#6c757d',
    marginBottom: '0.5rem',
  },
  offersList: {
    marginTop: '0.75rem',
    paddingTop: '0.75rem',
    borderTop: '1px solid #e9ecef',
  },
  offerItem: {
    fontSize: '0.75rem',
    color: '#495057',
    marginBottom: '0.5rem',
    lineHeight: '1.4',
  },
  offerBank: {
    fontWeight: 'bold' as const,
    color: '#007bff',
  },
  moreOffers: {
    fontSize: '0.75rem',
    color: '#007bff',
    fontStyle: 'italic' as const,
  },
  competitorItem: {
    marginBottom: '0.75rem',
    paddingBottom: '0.75rem',
    borderBottom: '1px solid #e9ecef',
  },
  competitorName: {
    fontSize: '0.875rem',
    fontWeight: 'bold' as const,
    color: '#495057',
  },
  competitorPrice: {
    fontSize: '1.125rem',
    fontWeight: 'bold' as const,
    color: '#17a2b8',
  },
  competitorAvailability: {
    fontSize: '0.75rem',
    color: '#6c757d',
  },
  allOffersSection: {
    marginTop: '1.5rem',
    paddingTop: '1.5rem',
    borderTop: '2px solid #dee2e6',
  },
  allOffersTitle: {
    fontSize: '1.125rem',
    fontWeight: 'bold' as const,
    color: '#232f3e',
    marginBottom: '1rem',
  },
  allOffersGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '1rem',
  },
  offerCard: {
    backgroundColor: 'white',
    padding: '1rem',
    borderRadius: '6px',
    border: '1px solid #dee2e6',
  },
  offerCardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  offerCardBank: {
    fontSize: '0.875rem',
    fontWeight: 'bold' as const,
    color: '#007bff',
  },
  offerCardType: {
    fontSize: '0.75rem',
    padding: '0.25rem 0.5rem',
    backgroundColor: '#e7f3ff',
    color: '#0056b3',
    borderRadius: '4px',
  },
  offerCardDescription: {
    fontSize: '0.875rem',
    color: '#495057',
    marginBottom: '0.5rem',
    lineHeight: '1.5',
  },
  offerCardTerms: {
    fontSize: '0.75rem',
    color: '#6c757d',
    fontStyle: 'italic' as const,
  },
};

export default PriceOverview;
