/**
 * TypeScript types for API models
 */

export interface Review {
  rating: string;
  title: string;
  text: string;
  date: string;
  verified_purchase: boolean;
  helpful_votes?: number;
}

export interface BankOffer {
  bank: string;
  offer_type: string; // e.g., 'Cashback', 'EMI', 'Discount', 'Exchange'
  description: string;
  terms?: string;
}

export interface PriceComparison {
  current_price: string;
  alternative_prices: Array<{
    site: string;
    price: string;
    url: string;
    availability: string;
  }>;
}

export interface ExternalReview {
  title: string;
  snippet: string;
  link: string;
  source: string;
}

export interface ComparisonArticle {
  title: string;
  snippet: string;
  link: string;
}

export interface IssueDiscussion {
  title: string;
  snippet: string;
  link: string;
}

export interface RedditDiscussion {
  title: string;
  snippet: string;
  link: string;
  subreddit?: string;
}

export interface VideoReview {
  title: string;
  link: string;
  source: string;
}

export interface NewsArticle {
  title: string;
  snippet: string;
  link: string;
  source: string;
  date?: string;
}

export interface WebSearchAnalysis {
  external_reviews: ExternalReview[];
  comparison_articles: ComparisonArticle[];
  issue_discussions: IssueDiscussion[];
  reddit_discussions: RedditDiscussion[];
  news_articles: NewsArticle[];
  video_reviews: VideoReview[];
  key_findings: string[];
  red_flags: string[];
  overall_sentiment: {
    sentiment: string;
    confidence: string;
    summary: string;
  };
}

export interface ProductData {
  product_id: string; // Generic product ID (ASIN for Amazon, FSN for Flipkart)
  asin?: string; // Amazon-specific ASIN (for backward compatibility)
  title: string;
  platform?: string; // e.g., 'Amazon', 'Flipkart'
  brand?: string;
  price?: string;
  rating?: string;
  ratings_count?: string;
  features?: string[];
  description?: string;
  specifications?: Record<string, string>;
  images?: string[];
  reviews: Review[];
  bank_offers?: BankOffer[];
  price_comparison?: PriceComparison;
  web_search_analysis?: WebSearchAnalysis;
}

// Request types
export interface ScrapeRequest {
  url: string;
  session_id?: string;
}

export interface ChatRequest {
  session_id: string;
  product_id: string;
  question: string;
}

export interface ClearChatRequest {
  session_id: string;
}

// Response types
export interface AnalysisResponse {
  success: boolean;
  message: string;
  analysis: string;
  product_data?: ProductData;
}

export interface ChatResponse {
  success: boolean;
  message: string;
  answer: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatHistoryResponse {
  success: boolean;
  message: string;
  history: ChatMessage[];
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export interface ErrorResponse {
  detail: string;
}
