/**
 * API client service
 */

import axios, { AxiosInstance } from 'axios';
import type {
  ScrapeRequest,
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
   * Scrape and analyze product in one call
   */
  async scrapeAndAnalyze(request: ScrapeRequest): Promise<AnalysisResponse> {
    const response = await this.client.post<AnalysisResponse>('/products/scrape-and-analyze', request);
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
