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
  const [currentImageIndex, setCurrentImageIndex] = React.useState(0);

  // Get platform name and icon
  const platformName = product.platform || 'Amazon'; // Default to Amazon if not specified
  const platformIcon = platformName === 'Flipkart' ? '🛍️' : '🛒';

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

  // Calculate minimum price with best bank offer
  const bestOffer = otherOffers.reduce((best, offer) => {
    const discount = (offer as any).discount_amount || 0;
    const bestDiscount = (best as any)?.discount_amount || 0;
    return discount > bestDiscount ? offer : best;
  }, otherOffers[0]);

  const bestDiscount = (bestOffer as any)?.discount_amount || 0;

  const minPriceWithOffer = basePrice > 0 && bestDiscount > 0
    ? basePrice - bestDiscount
    : basePrice;

  const formatPrice = (price: number): string => {
    return price > 0 ? `₹${price.toLocaleString('en-IN')}` : 'N/A';
  };

  // Get competitor prices - check multiple possible locations and filter out the source platform
  const allCompetitorPrices = (product as any).competitor_prices ||
                              product.price_comparison?.alternative_prices ||
                              [];
  const competitorPrices = allCompetitorPrices.filter((comp: any) =>
    !comp.site.toLowerCase().includes(platformName.toLowerCase())
  );

  // Get product images
  const productImages = product.images || [];
  const hasImages = productImages.length > 0;

  // Carousel navigation
  const nextImage = () => {
    setCurrentImageIndex((prev) => (prev + 1) % productImages.length);
  };

  const prevImage = () => {
    setCurrentImageIndex((prev) => (prev - 1 + productImages.length) % productImages.length);
  };

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

      {/* Pricing Section with Image Carousel */}
      <div style={styles.pricingSection}>
        <h2 style={styles.sectionTitle}>💰 Product & Pricing Overview</h2>

        <div style={styles.pricingSplitContainer}>
          {/* Left Half: Image Carousel */}
          <div style={styles.imageCarouselContainer}>
            {hasImages ? (
              <>
                <div style={styles.carouselImageWrapper}>
                  <img
                    src={productImages[currentImageIndex]}
                    alt={`${product.title} - ${currentImageIndex + 1}`}
                    style={styles.carouselImage}
                  />

                  {/* Navigation Buttons */}
                  {productImages.length > 1 && (
                    <>
                      <button
                        onClick={prevImage}
                        style={{...styles.carouselButton, ...styles.carouselButtonPrev}}
                      >
                        ‹
                      </button>
                      <button
                        onClick={nextImage}
                        style={{...styles.carouselButton, ...styles.carouselButtonNext}}
                      >
                        ›
                      </button>
                    </>
                  )}
                </div>

                {/* Thumbnail Navigation */}
                {productImages.length > 1 && (
                  <div style={styles.thumbnailContainer}>
                    {productImages.map((img, idx) => (
                      <div
                        key={idx}
                        onClick={() => setCurrentImageIndex(idx)}
                        style={{
                          ...styles.thumbnail,
                          ...(idx === currentImageIndex ? styles.thumbnailActive : {})
                        }}
                      >
                        <img src={img} alt={`Thumbnail ${idx + 1}`} style={styles.thumbnailImage} />
                      </div>
                    ))}
                  </div>
                )}

                {/* Image Counter */}
                <div style={styles.imageCounter}>
                  {currentImageIndex + 1} / {productImages.length}
                </div>
              </>
            ) : (
              <div style={styles.noImagePlaceholder}>
                <div style={styles.noImageIcon}>📷</div>
                <div style={styles.noImageText}>No images available</div>
              </div>
            )}
          </div>

          {/* Right Half: Pricing & Offers */}
          <div style={styles.pricingContainer}>
            {/* Pricing Cards */}
            <div style={styles.priceGrid}>
              {/* Platform Pricing Card */}
              <div style={{...styles.priceCard, ...styles.priceCardMain}}>
                <div style={styles.priceCardHeader}>
                  <div style={styles.priceLabel}>{platformIcon} {platformName} Price</div>
                </div>

                <div style={styles.pricingRows}>
                  {/* Regular Price */}
                  <div style={styles.pricingRow}>
                    <div style={styles.pricingRowLabel}>Regular Price:</div>
                    <div style={styles.pricingRowValue}>{product.price || 'N/A'}</div>
                  </div>

                  {/* Best Price with Offers */}
                  {otherOffers.length > 0 && bestDiscount > 0 && (
                    <div style={{...styles.pricingRow, ...styles.pricingRowHighlight}}>
                      <div style={styles.pricingRowLabel}>Best Price:</div>
                      <div style={styles.pricingRowValueBest}>
                        {formatPrice(minPriceWithOffer)}
                        <span style={styles.savingsTextInline}>
                          (Save ₹{bestDiscount.toLocaleString('en-IN')})
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Best Offer Badge */}
                {bestOffer && bestDiscount > 0 && (
                  <div style={styles.bestOfferBadge}>
                    💳 {bestOffer.bank || 'Bank'} {bestOffer.offer_type}
                  </div>
                )}
              </div>

              {/* Competitor Prices */}
              {competitorPrices.length > 0 && (
                <div style={styles.priceCard}>
                  <div style={styles.priceLabel}>🔍 Competitor Prices</div>
                  <div style={styles.competitorList}>
                    {competitorPrices.map((competitor, idx) => (
                      <a
                        key={idx}
                        href={competitor.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={styles.competitorLink}
                      >
                        <div style={styles.competitorItem}>
                          <div style={styles.competitorSite}>{competitor.site}</div>
                          <div style={styles.competitorPrice}>{competitor.price}</div>
                        </div>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Bank Offers - Below Pricing in Right Column */}
            {bankOffers.length > 0 && (
              <div style={styles.offersInRightColumn}>
                <h3 style={styles.offersRightColumnTitle}>💳 Available Offers</h3>
                <div style={styles.offersRightColumnScroll}>
                  {bankOffers.map((offer, idx) => (
                    <div key={idx} style={styles.offerCardVertical}>
                      <div style={styles.offerHeader}>
                        <span style={styles.offerBank}>{offer.bank || 'Generic Offer'}</span>
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
        </div>
      </div>

      {/* Full Analysis Section */}
      <div style={styles.analysisSection}>
        <h2 style={styles.sectionTitle}>📊 Complete Analysis</h2>
        <div style={styles.analysisContent}>
          <div style={{
            wordWrap: 'break-word',
            overflowWrap: 'anywhere',
            wordBreak: 'break-word',
            whiteSpace: 'pre-wrap',
            maxWidth: '100%',
          }}>
            <ReactMarkdown
              components={{
                p: ({children}) => <p style={{margin: '1em 0', wordWrap: 'break-word', overflowWrap: 'anywhere'}}>{children}</p>,
                pre: ({children}) => <pre style={{whiteSpace: 'pre-wrap', wordWrap: 'break-word', overflowWrap: 'anywhere', maxWidth: '100%', overflow: 'auto'}}>{children}</pre>,
                code: ({children}) => <code style={{whiteSpace: 'pre-wrap', wordWrap: 'break-word', overflowWrap: 'anywhere'}}>{children}</code>,
              }}
            >
              {analysis}
            </ReactMarkdown>
          </div>
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
    maxWidth: '100%',
    width: '100%',
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

  // Image Carousel
  pricingSplitContainer: {
    display: 'flex',
    gap: '2rem',
    flexWrap: 'wrap' as const,
    marginBottom: '2rem',
  },
  imageCarouselContainer: {
    flex: '1 1 45%',
    minWidth: '300px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '1rem',
  },
  carouselImageWrapper: {
    position: 'relative' as const,
    width: '100%',
    paddingBottom: '100%',
    backgroundColor: '#f5f5f5',
    borderRadius: '8px',
    overflow: 'hidden',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  carouselImage: {
    position: 'absolute' as const,
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    objectFit: 'contain' as const,
  },
  carouselButton: {
    position: 'absolute' as const,
    top: '50%',
    transform: 'translateY(-50%)',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    border: 'none',
    borderRadius: '50%',
    width: '40px',
    height: '40px',
    fontSize: '24px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
    transition: 'all 0.3s ease',
    zIndex: 10,
  },
  carouselButtonPrev: {
    left: '10px',
  },
  carouselButtonNext: {
    right: '10px',
  },
  thumbnailContainer: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(60px, 1fr))',
    gap: '0.5rem',
  },
  thumbnail: {
    width: '100%',
    paddingBottom: '100%',
    position: 'relative' as const,
    cursor: 'pointer',
    borderRadius: '4px',
    overflow: 'hidden',
    border: '2px solid transparent',
    transition: 'border-color 0.2s ease',
  },
  thumbnailActive: {
    borderColor: '#667eea',
  },
  thumbnailImage: {
    position: 'absolute' as const,
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    objectFit: 'cover' as const,
  },
  imageCounter: {
    textAlign: 'center' as const,
    fontSize: '0.875rem',
    color: '#666',
    fontWeight: '500' as const,
  },
  noImagePlaceholder: {
    width: '100%',
    paddingBottom: '100%',
    position: 'relative' as const,
    backgroundColor: '#f5f5f5',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'column' as const,
  },
  noImageIcon: {
    position: 'absolute' as const,
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    fontSize: '4rem',
    opacity: 0.3,
  },
  noImageText: {
    position: 'absolute' as const,
    top: '60%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    fontSize: '1rem',
    color: '#999',
    marginTop: '1rem',
  },
  pricingContainer: {
    flex: '1 1 45%',
    minWidth: '300px',
  },

  priceGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '1rem',
  },
  priceCard: {
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    border: '2px solid #e0e0e0',
    textAlign: 'center' as const,
  },
  priceCardMain: {
    border: '2px solid #4CAF50',
    backgroundColor: '#f1f8f4',
  },
  priceCardHeader: {
    marginBottom: '1rem',
  },
  priceCardHighlight: {
    borderColor: '#4CAF50',
    backgroundColor: '#f1f8f4',
  },
  pricingRows: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '1rem',
    marginBottom: '1rem',
  },
  pricingRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.75rem',
    backgroundColor: 'white',
    borderRadius: '6px',
  },
  pricingRowHighlight: {
    backgroundColor: '#e8f5e9',
    border: '1px solid #4CAF50',
  },
  pricingRowLabel: {
    fontSize: '0.875rem',
    color: '#666',
    fontWeight: '600' as const,
  },
  pricingRowValue: {
    fontSize: '1.5rem',
    fontWeight: 'bold' as const,
    color: '#2c3e50',
  },
  pricingRowValueBest: {
    fontSize: '1.5rem',
    fontWeight: 'bold' as const,
    color: '#2e7d32',
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'flex-end',
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
  savingsText: {
    fontSize: '1rem',
    color: '#4CAF50',
    fontWeight: '600' as const,
    marginTop: '0.5rem',
  },
  savingsTextInline: {
    fontSize: '0.875rem',
    color: '#2e7d32',
    fontWeight: '500' as const,
    marginTop: '0.25rem',
  },
  bestOfferBadge: {
    marginTop: '1rem',
    fontSize: '0.85rem',
    padding: '0.75rem 1rem',
    backgroundColor: '#e8f5e9',
    color: '#2e7d32',
    borderRadius: '8px',
    fontWeight: '600' as const,
    textAlign: 'center' as const,
    border: '1px solid #4CAF50',
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
  competitorLink: {
    textDecoration: 'none',
    display: 'block',
    transition: 'all 0.2s ease',
    borderRadius: '4px',
  },
  competitorItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.75rem',
    borderBottom: '1px solid #e0e0e0',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    backgroundColor: 'transparent',
  },
  competitorSite: {
    fontSize: '0.875rem',
    fontWeight: '500' as const,
    color: '#1976d2',
  },
  competitorPrice: {
    fontSize: '1.125rem',
    fontWeight: 'bold' as const,
    color: '#2c3e50',
  },

  // Offers in Right Column (Below Pricing) - Horizontal Carousel
  offersInRightColumn: {
    marginTop: '1rem',
  },
  offersRightColumnTitle: {
    fontSize: '1.1rem',
    fontWeight: 'bold' as const,
    marginBottom: '1rem',
    color: '#2c3e50',
    margin: '0 0 1rem 0',
  },
  offersRightColumnScroll: {
    display: 'flex',
    flexDirection: 'row' as const,
    gap: '1rem',
    overflowX: 'auto' as const,
    paddingBottom: '1rem',
    scrollbarWidth: 'thin' as const,
    scrollbarColor: '#1976d2 #f1f8f4',
  },
  offerCardVertical: {
    backgroundColor: 'white',
    padding: '1rem',
    borderRadius: '8px',
    border: '2px solid #1976d2',
    minWidth: '280px',
    maxWidth: '280px',
    flexShrink: 0,
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },

  // Old styles (kept for compatibility)
  offersInColumn: {
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    border: '2px solid #e0e0e0',
  },
  offersColumnTitle: {
    fontSize: '1.1rem',
    fontWeight: 'bold' as const,
    marginBottom: '1rem',
    color: '#2c3e50',
    margin: '0 0 1rem 0',
  },
  offersColumnScroll: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.75rem',
    maxHeight: '400px',
    overflowY: 'auto' as const,
    paddingRight: '0.5rem',
  },
  offerCardCompact: {
    backgroundColor: '#f8f9fa',
    padding: '1rem',
    borderRadius: '6px',
    border: '1px solid #1976d2',
  },

  // All Offers
  allOffersSection: {
    marginTop: '2rem',
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
  offersCarouselWrapper: {
    overflow: 'hidden',
    position: 'relative' as const,
  },
  offersCarouselScroll: {
    display: 'flex',
    gap: '1rem',
    overflowX: 'auto' as const,
    paddingBottom: '1rem',
    scrollbarWidth: 'thin' as const,
    scrollbarColor: '#1976d2 #f1f8f4',
  },
  offerCardCarousel: {
    backgroundColor: 'white',
    padding: '1rem',
    borderRadius: '8px',
    border: '2px solid #1976d2',
    minWidth: '300px',
    maxWidth: '300px',
    flexShrink: 0,
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
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

  // Analysis Section
  analysisSection: {
    padding: '2rem',
    backgroundColor: 'white',
  },
  analysisContent: {
    fontSize: '1rem',
    lineHeight: 1.8,
    color: '#333',
    wordWrap: 'break-word' as const,
    overflowWrap: 'break-word' as const,
    wordBreak: 'break-word' as const,
    whiteSpace: 'normal' as const,
    maxWidth: '100%',
    overflow: 'hidden',
  },
};

export default ProductAnalysisView;
