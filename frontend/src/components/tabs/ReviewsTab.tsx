/**
 * Reviews tab component
 */

import React, { useState } from 'react';
import { useProduct } from '@/contexts/ProductContext';
import type { Review, ExternalReview } from '@/types';

interface ReviewsTabProps {
  activeView: 'platform' | 'external' | 'summary';
}

// Helper function to extract YouTube video ID from URL
const getYouTubeVideoId = (url: string): string | null => {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
    /youtube\.com\/shorts\/([^&\n?#]+)/
  ];

  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) return match[1];
  }

  return null;
};

// YouTube embed component
const YouTubeEmbed: React.FC<{ url: string; title: string }> = ({ url, title }) => {
  const videoId = getYouTubeVideoId(url);

  if (!videoId) return null;

  return (
    <div style={styles.videoContainer}>
      <iframe
        width="100%"
        height="315"
        src={`https://www.youtube.com/embed/${videoId}`}
        title={title}
        frameBorder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
        style={styles.videoIframe}
      />
    </div>
  );
};

const ReviewsTab: React.FC<ReviewsTabProps> = ({ activeView }) => {
  const { productData } = useProduct();
  const [ratingFilter, setRatingFilter] = useState<number>(0);
  const [verifiedOnly, setVerifiedOnly] = useState<boolean>(false);

  if (!productData) {
    return (
      <div style={styles.emptyState}>
        <p>Please scrape a product first to view reviews.</p>
      </div>
    );
  }

  // Get platform name and icon
  const platformName = productData.platform || 'Amazon';
  const platformIcon = platformName === 'Flipkart' ? '🛍️' : '🛒';

  const platformReviews = productData.reviews || [];
  const webSearch = productData.web_search_analysis;

  // Filter platform reviews (no removal, just apply user filters)
  const filteredReviews = platformReviews.filter((review) => {
    const rating = parseFloat(review.rating.split(' ')[0] || '0');
    if (ratingFilter > 0 && rating !== ratingFilter) return false;
    if (verifiedOnly && !review.verified_purchase) return false;
    return true;
  });

  // Merge external reviews, comparisons, Reddit discussions, and news articles
  const externalReviews = webSearch?.external_reviews || [];
  const comparisonArticles = webSearch?.comparison_articles || [];
  const redditDiscussions = webSearch?.reddit_discussions || [];
  const newsArticles = webSearch?.news_articles || [];
  const mergedExternalContent = [
    ...externalReviews.map(r => ({ ...r, type: 'review' as const })),
    ...comparisonArticles.map(c => ({ ...c, type: 'comparison' as const, source: 'Comparison Article' })),
    ...redditDiscussions.map(rd => ({ ...rd, type: 'reddit' as const })),
    ...newsArticles.map(na => ({ ...na, type: 'news' as const }))
  ];

  return (
    <div style={styles.container}>
      {/* Platform Reviews */}
      {activeView === 'platform' && (
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

      {/* External Reviews, Comparisons, Reddit & News (Merged) */}
      {activeView === 'external' && (
        <div style={styles.content}>
          {mergedExternalContent.length > 0 ? (
            <div style={styles.reviewsList}>
              {mergedExternalContent.map((item, idx) => {
                const isYouTube = getYouTubeVideoId(item.link) !== null;

                return (
                  <div key={idx} style={styles.externalCard}>
                    <div style={styles.externalHeader}>
                      <span style={
                        item.type === 'review' ? styles.reviewBadge :
                        item.type === 'comparison' ? styles.comparisonBadge :
                        item.type === 'reddit' ? styles.redditBadge :
                        styles.newsBadge
                      }>
                        {item.type === 'review' ? '📝 Review' :
                         item.type === 'comparison' ? '🔍 Comparison' :
                         item.type === 'reddit' ? '💬 Reddit Discussion' :
                         '📰 News Article'}
                      </span>
                      {isYouTube && (
                        <span style={styles.youtubeBadge}>
                          🎥 Video
                        </span>
                      )}
                      {item.type === 'news' && (item as any).date && (
                        <span style={styles.dateTag}>{(item as any).date}</span>
                      )}
                    </div>
                    <h4 style={styles.externalTitle}>{item.title}</h4>
                    <p style={styles.externalSnippet}>{item.snippet}</p>

                    {/* Inline YouTube video if it's a YouTube link */}
                    {isYouTube && <YouTubeEmbed url={item.link} title={item.title} />}

                    <div style={styles.externalFooter}>
                      <span style={styles.source}>
                        Source: {item.type === 'reddit' && (item as any).subreddit
                          ? `r/${(item as any).subreddit}`
                          : item.source}
                      </span>
                      <a
                        href={item.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={styles.link}
                      >
                        {isYouTube ? 'Watch on YouTube →' :
                         item.type === 'reddit' ? 'View Discussion →' :
                         item.type === 'news' ? 'Read Article →' :
                         'Read More →'}
                      </a>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p style={styles.noResults}>
              No external reviews, comparisons, Reddit discussions, or news found. Run analysis with "Include External Reviews" enabled.
            </p>
          )}
        </div>
      )}

      {/* Summary */}
      {activeView === 'summary' && (
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
  externalHeader: {
    marginBottom: '0.75rem',
  },
  reviewBadge: {
    display: 'inline-block',
    padding: '0.25rem 0.75rem',
    backgroundColor: '#4caf50',
    color: 'white',
    borderRadius: '12px',
    fontSize: '0.75rem',
    fontWeight: '600',
  },
  comparisonBadge: {
    display: 'inline-block',
    padding: '0.25rem 0.75rem',
    backgroundColor: '#2196f3',
    color: 'white',
    borderRadius: '12px',
    fontSize: '0.75rem',
    fontWeight: '600',
  },
  redditBadge: {
    display: 'inline-block',
    padding: '0.25rem 0.75rem',
    backgroundColor: '#ff4500',
    color: 'white',
    borderRadius: '12px',
    fontSize: '0.75rem',
    fontWeight: '600',
  },
  newsBadge: {
    display: 'inline-block',
    padding: '0.25rem 0.75rem',
    backgroundColor: '#9c27b0',
    color: 'white',
    borderRadius: '12px',
    fontSize: '0.75rem',
    fontWeight: '600',
  },
  youtubeBadge: {
    display: 'inline-block',
    padding: '0.25rem 0.75rem',
    backgroundColor: '#ff0000',
    color: 'white',
    borderRadius: '12px',
    fontSize: '0.75rem',
    fontWeight: '600',
    marginLeft: '0.5rem',
  },
  dateTag: {
    display: 'inline-block',
    padding: '0.25rem 0.5rem',
    backgroundColor: '#e0e0e0',
    color: '#666',
    borderRadius: '8px',
    fontSize: '0.7rem',
    marginLeft: '0.5rem',
  },
  videoContainer: {
    margin: '1rem 0',
    borderRadius: '8px',
    overflow: 'hidden',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  videoIframe: {
    borderRadius: '8px',
    display: 'block',
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
