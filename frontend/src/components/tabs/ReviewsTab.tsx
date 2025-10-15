/**
 * Reviews tab component
 */

import React, { useState } from 'react';
import { useProduct } from '@/contexts/ProductContext';
import type { Review, ExternalReview } from '@/types';

const ReviewsTab: React.FC = () => {
  const { productData } = useProduct();
  const [activeSubTab, setActiveSubTab] = useState<'amazon' | 'external' | 'comparisons' | 'summary'>('amazon');
  const [ratingFilter, setRatingFilter] = useState<number>(0);
  const [verifiedOnly, setVerifiedOnly] = useState<boolean>(false);

  if (!productData) {
    return (
      <div style={styles.emptyState}>
        <p>Please scrape a product first to view reviews.</p>
      </div>
    );
  }

  const amazonReviews = productData.reviews || [];
  const webSearch = productData.web_search_analysis;

  // Filter Amazon reviews
  const filteredReviews = amazonReviews.filter((review) => {
    const rating = parseFloat(review.rating.split(' ')[0] || '0');
    if (ratingFilter > 0 && rating !== ratingFilter) return false;
    if (verifiedOnly && !review.verified_purchase) return false;
    return true;
  });

  return (
    <div style={styles.container}>
      {/* Sub-tabs */}
      <div style={styles.subTabs}>
        <button
          onClick={() => setActiveSubTab('amazon')}
          style={activeSubTab === 'amazon' ? { ...styles.subTab, ...styles.subTabActive } : styles.subTab}
        >
          🛒 Amazon Reviews ({amazonReviews.length})
        </button>
        <button
          onClick={() => setActiveSubTab('external')}
          style={activeSubTab === 'external' ? { ...styles.subTab, ...styles.subTabActive } : styles.subTab}
        >
          🌐 External Reviews ({webSearch?.external_reviews?.length || 0})
        </button>
        <button
          onClick={() => setActiveSubTab('comparisons')}
          style={activeSubTab === 'comparisons' ? { ...styles.subTab, ...styles.subTabActive } : styles.subTab}
        >
          🔍 Comparisons ({webSearch?.comparison_articles?.length || 0})
        </button>
        <button
          onClick={() => setActiveSubTab('summary')}
          style={activeSubTab === 'summary' ? { ...styles.subTab, ...styles.subTabActive } : styles.subTab}
        >
          📊 Summary
        </button>
      </div>

      {/* Amazon Reviews */}
      {activeSubTab === 'amazon' && (
        <div style={styles.content}>
          <div style={styles.filters}>
            <div style={styles.filterGroup}>
              <label>Filter by rating:</label>
              <select
                value={ratingFilter}
                onChange={(e) => setRatingFilter(Number(e.target.value))}
                style={styles.select}
              >
                <option value={0}>All Ratings</option>
                <option value={5}>⭐⭐⭐⭐⭐ (5 stars)</option>
                <option value={4}>⭐⭐⭐⭐ (4 stars)</option>
                <option value={3}>⭐⭐⭐ (3 stars)</option>
                <option value={2}>⭐⭐ (2 stars)</option>
                <option value={1}>⭐ (1 star)</option>
              </select>
            </div>
            <label style={styles.checkbox}>
              <input
                type="checkbox"
                checked={verifiedOnly}
                onChange={(e) => setVerifiedOnly(e.target.checked)}
              />
              <span>Verified purchases only</span>
            </label>
          </div>

          <div style={styles.reviewsList}>
            {filteredReviews.length > 0 ? (
              filteredReviews.map((review, idx) => (
                <div key={idx} style={styles.reviewCard}>
                  <div style={styles.reviewHeader}>
                    <span style={styles.rating}>{review.rating}</span>
                    {review.verified_purchase && (
                      <span style={styles.verified}>✓ Verified Purchase</span>
                    )}
                    <span style={styles.date}>{review.date}</span>
                  </div>
                  <h4 style={styles.reviewTitle}>{review.title}</h4>
                  <p style={styles.reviewText}>{review.text}</p>
                </div>
              ))
            ) : (
              <p style={styles.noResults}>No reviews match the selected filters.</p>
            )}
          </div>
        </div>
      )}

      {/* External Reviews */}
      {activeSubTab === 'external' && (
        <div style={styles.content}>
          {webSearch?.external_reviews && webSearch.external_reviews.length > 0 ? (
            <div style={styles.reviewsList}>
              {webSearch.external_reviews.map((review, idx) => (
                <div key={idx} style={styles.externalCard}>
                  <h4 style={styles.externalTitle}>{review.title}</h4>
                  <p style={styles.externalSnippet}>{review.snippet}</p>
                  <div style={styles.externalFooter}>
                    <span style={styles.source}>Source: {review.source}</span>
                    <a
                      href={review.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={styles.link}
                    >
                      Read More →
                    </a>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={styles.noResults}>
              No external reviews found. Run analysis with "Include External Reviews" enabled.
            </p>
          )}
        </div>
      )}

      {/* Comparisons */}
      {activeSubTab === 'comparisons' && (
        <div style={styles.content}>
          {webSearch?.comparison_articles && webSearch.comparison_articles.length > 0 ? (
            <div style={styles.reviewsList}>
              {webSearch.comparison_articles.map((article, idx) => (
                <div key={idx} style={styles.externalCard}>
                  <h4 style={styles.externalTitle}>{article.title}</h4>
                  <p style={styles.externalSnippet}>{article.snippet}</p>
                  <a
                    href={article.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={styles.link}
                  >
                    Read Comparison →
                  </a>
                </div>
              ))}
            </div>
          ) : (
            <p style={styles.noResults}>
              No comparisons found. Run analysis with "Include External Reviews" enabled.
            </p>
          )}
        </div>
      )}

      {/* Summary */}
      {activeSubTab === 'summary' && (
        <div style={styles.content}>
          {webSearch ? (
            <>
              {webSearch.key_findings && webSearch.key_findings.length > 0 && (
                <div style={styles.summarySection}>
                  <h3 style={styles.summaryTitle}>✨ Key Findings</h3>
                  <ul style={styles.findingsList}>
                    {webSearch.key_findings.map((finding, idx) => (
                      <li key={idx} style={styles.findingItem}>{finding}</li>
                    ))}
                  </ul>
                </div>
              )}

              {webSearch.red_flags && webSearch.red_flags.length > 0 && (
                <div style={styles.summarySection}>
                  <h3 style={styles.summaryTitle}>🚩 Red Flags</h3>
                  <ul style={styles.redFlagsList}>
                    {webSearch.red_flags.map((flag, idx) => (
                      <li key={idx} style={styles.redFlagItem}>{flag}</li>
                    ))}
                  </ul>
                </div>
              )}

              {webSearch.overall_sentiment && (
                <div style={styles.summarySection}>
                  <h3 style={styles.summaryTitle}>💭 Overall Sentiment</h3>
                  <div style={styles.sentimentCard}>
                    <div style={styles.sentimentBadge}>
                      {webSearch.overall_sentiment.sentiment}
                    </div>
                    <p>{webSearch.overall_sentiment.summary}</p>
                  </div>
                </div>
              )}
            </>
          ) : (
            <p style={styles.noResults}>
              No summary available. Run analysis with "Include External Reviews" enabled.
            </p>
          )}
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
  subTabs: {
    display: 'flex',
    gap: '0.5rem',
    marginBottom: '1.5rem',
    borderBottom: '2px solid #e0e0e0',
  },
  subTab: {
    padding: '0.75rem 1.5rem',
    backgroundColor: 'transparent',
    border: 'none',
    borderBottom: '3px solid transparent',
    cursor: 'pointer',
    fontSize: '1rem',
    color: '#666',
  },
  subTabActive: {
    borderBottomColor: '#ff9900',
    color: '#232f3e',
    fontWeight: '600',
  },
  content: {
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  filters: {
    display: 'flex',
    gap: '2rem',
    marginBottom: '1.5rem',
    padding: '1rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
  },
  filterGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  select: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
  },
  checkbox: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    cursor: 'pointer',
  },
  reviewsList: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '1rem',
  },
  reviewCard: {
    padding: '1rem',
    border: '1px solid #e0e0e0',
    borderRadius: '4px',
    backgroundColor: '#fafafa',
  },
  reviewHeader: {
    display: 'flex',
    gap: '1rem',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  rating: {
    fontWeight: '600',
    color: '#ff9900',
  },
  verified: {
    fontSize: '0.875rem',
    color: '#00a814',
  },
  date: {
    fontSize: '0.875rem',
    color: '#666',
    marginLeft: 'auto',
  },
  reviewTitle: {
    margin: '0 0 0.5rem',
    fontSize: '1rem',
    fontWeight: '600',
  },
  reviewText: {
    margin: '0',
    lineHeight: '1.6',
    color: '#333',
  },
  externalCard: {
    padding: '1.5rem',
    border: '1px solid #e0e0e0',
    borderRadius: '4px',
    backgroundColor: '#fafafa',
  },
  externalTitle: {
    margin: '0 0 0.75rem',
    fontSize: '1.1rem',
    color: '#232f3e',
  },
  externalSnippet: {
    margin: '0 0 1rem',
    lineHeight: '1.6',
    color: '#333',
  },
  externalFooter: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  source: {
    fontSize: '0.875rem',
    color: '#666',
  },
  link: {
    color: '#007bff',
    textDecoration: 'none',
    fontWeight: '600',
  },
  noResults: {
    textAlign: 'center' as const,
    padding: '2rem',
    color: '#666',
  },
  summarySection: {
    marginBottom: '2rem',
  },
  summaryTitle: {
    margin: '0 0 1rem',
    fontSize: '1.3rem',
    color: '#232f3e',
  },
  findingsList: {
    margin: '0',
    paddingLeft: '1.5rem',
  },
  findingItem: {
    marginBottom: '0.75rem',
    lineHeight: '1.6',
  },
  redFlagsList: {
    margin: '0',
    paddingLeft: '1.5rem',
  },
  redFlagItem: {
    marginBottom: '0.75rem',
    lineHeight: '1.6',
    color: '#d32f2f',
  },
  sentimentCard: {
    padding: '1rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
  },
  sentimentBadge: {
    display: 'inline-block',
    padding: '0.5rem 1rem',
    backgroundColor: '#ff9900',
    color: 'white',
    borderRadius: '20px',
    fontWeight: '600',
    marginBottom: '0.75rem',
  },
};

export default ReviewsTab;
