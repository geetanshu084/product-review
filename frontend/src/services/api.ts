/**
 * API client service
 */

import axios, { AxiosInstance } from 'axios';
import type {
  ScrapeRequest,
  ScrapeResponse,
  AnalyzeRequest,
  AnalysisResponse,
  ChatRequest,
  ChatResponse,
  ClearChatRequest,
  ChatHistoryResponse,
  ProductData,
  HealthResponse,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_V1_PREFIX = '/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}${API_V1_PREFIX}`,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 120000, // 2 minutes for scraping/analysis
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        throw error;
      }
    );
  }

  // Health check
  async healthCheck(): Promise<HealthResponse> {
    const response = await axios.get<HealthResponse>(`${API_BASE_URL}/health`);
    return response.data;
  }

  // Product endpoints

  /**
   * Unified endpoint: Scrape and analyze product in one call
   * This is the recommended method that runs the complete pipeline
   */
  async scrapeAndAnalyze(request: ScrapeRequest): Promise<AnalysisResponse> {
    const response = await this.client.post<AnalysisResponse>('/products/scrape-and-analyze', request);
    return response.data;
  }

  /**
   * Legacy: Scrape product only (without analysis)
   */
  async scrapeProduct(request: ScrapeRequest): Promise<ScrapeResponse> {
    const response = await this.client.post<ScrapeResponse>('/products/scrape', request);
    return response.data;
  }

  /**
   * Legacy: Analyze already-scraped product
   */
  async analyzeProduct(request: AnalyzeRequest): Promise<AnalysisResponse> {
    const response = await this.client.post<AnalysisResponse>('/products/analyze', request);
    return response.data;
  }

  async getProduct(asin: string): Promise<ProductData> {
    const response = await this.client.get<ProductData>(`/products/product/${asin}`);
    return response.data;
  }

  // Chat endpoints
  async askQuestion(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.client.post<ChatResponse>('/chat/ask', request);
    return response.data;
  }

  async getChatHistory(sessionId: string): Promise<ChatHistoryResponse> {
    const response = await this.client.get<ChatHistoryResponse>(`/chat/history/${sessionId}`);
    return response.data;
  }

  async clearChat(request: ClearChatRequest): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/chat/clear', request);
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
