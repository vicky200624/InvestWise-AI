import axios from 'axios';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Add JWT Auth interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.warn('Unauthorized or session expired');
    }
    return Promise.reject(error);
  }
);

export interface DashboardSummary {
  total_invested: number;
  current_value: number;
  overall_score: number;
  xirr: number;
  last_synced: string | null;
  allocation: Array<{ name: string; value: number }>;
  performance: Array<{ month: string; return: number }>;
}

export interface AssetHolding {
  id?: number;
  asset_type: string;
  symbol: string;
  name: string;
  code?: string;
  qty: number;
  avg_price: number;
  added_at?: string;
}

export interface StockAnalysisResult {
  task_id?: string;
  status?: string;
  analysis_id?: number;
  score?: number;
  action?: string;
  fundamental?: number;
  quant?: number;
  sentiment?: number;
  narrative?: string;
  top_factors?: string[];
  error?: string;
}

export const portfolioApi = {
  getDashboardSummary: async (): Promise<DashboardSummary> => {
    const response = await api.get('/api/dashboard/');
    return response.data;
  },
  getHoldings: async (): Promise<AssetHolding[]> => {
    const response = await api.get('/api/v1/portfolio/holdings/');
    return response.data;
  },
  optimizePortfolio: async (targetRisk: string = 'MODERATE') => {
    const response = await api.post('/api/portfolio/optimize/', { target_risk: targetRisk });
    return response.data;
  },
};

export const researchApi = {
  runAnalysis: async (symbol: string, timeHorizon: string = 'LONG'): Promise<StockAnalysisResult> => {
    const response = await api.post('/api/research/run/', {
      symbol,
      time_horizon: timeHorizon,
    });
    return response.data;
  },
  submitFeedback: async (analysisId: number, feedbackType: string, comment: string = '') => {
    const response = await api.post('/api/research/feedback/', {
      analysis: analysisId,
      feedback_type: feedbackType,
      comment,
    });
    return response.data;
  },
};

export const chatApi = {
  sendTextMessage: async (message: string, sessionId?: number) => {
    const response = await api.post('/api/langchain-chat/', {
      message,
      session_id: sessionId,
    });
    return response.data;
  },
  sendVoiceMessage: async (audioFile?: File, textFallback?: string) => {
    const formData = new FormData();
    if (audioFile) {
      formData.append('audio', audioFile);
    }
    if (textFallback) {
      formData.append('message', textFallback);
    }
    const response = await api.post('/api/voice-chat/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export const watchlistApi = {
  getWatchlist: async () => {
    const response = await api.get('/api/watchlist/');
    return response.data;
  },
};

export default api;
