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

// Response interceptor for error handling and automatic JWT refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh/`, {
            refresh: refreshToken,
          });
          const newAccessToken = res.data.access;
          localStorage.setItem('access_token', newAccessToken);
          if (res.data.refresh) {
            localStorage.setItem('refresh_token', res.data.refresh);
          }
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          }
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          return Promise.reject(refreshError);
        }
      }
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
  addHolding: async (data: AssetHolding): Promise<AssetHolding> => {
    const response = await api.post('/api/v1/portfolio/holdings/', data);
    return response.data;
  },
  deleteHolding: async (id: number) => {
    const response = await api.delete(`/api/v1/portfolio/holdings/${id}/`);
    return response.data;
  },
  optimizePortfolio: async (targetRisk: string = 'MODERATE') => {
    const response = await api.post('/api/portfolio/optimize/', { target_risk: targetRisk });
    return response.data;
  },
  syncBroker: async () => {
    const response = await api.post('/api/portfolio/sync-broker/');
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
  getItems: async () => {
    const response = await api.get('/api/watchlist/items/');
    return response.data;
  },
  addItem: async (symbol: string, watchlistId?: number) => {
    const response = await api.post('/api/watchlist/items/', {
      symbol: symbol.toUpperCase(),
      watchlist: watchlistId,
    });
    return response.data;
  },
  removeItem: async (id: number) => {
    const response = await api.delete(`/api/watchlist/items/${id}/`);
    return response.data;
  },
};


export interface UserProfile {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
}

export interface BrokerCredentialsInfo {
  id?: number;
  broker_name: string;
  client_id: string;
  is_active?: boolean;
  connected_at?: string;
  api_key?: string;
  pin?: string;
  totp_secret?: string;
}

export const authApi = {
  login: async (usernameOrEmail: string, password: string) => {
    const response = await api.post('/api/v1/auth/login/', {
      username: usernameOrEmail,
      password,
    });
    if (response.data?.access) {
      localStorage.setItem('access_token', response.data.access);
    }
    if (response.data?.refresh) {
      localStorage.setItem('refresh_token', response.data.refresh);
    }
    return response.data;
  },
  register: async (username: string, email: string, password: string) => {
    const response = await api.post('/api/v1/auth/register/', {
      username,
      email,
      password,
      password_confirm: password,
    });
    return response.data;
  },
  getProfile: async (): Promise<UserProfile> => {
    const response = await api.get('/api/v1/auth/profile/');
    return response.data;
  },
  logout: async () => {
    try {
      await api.post('/api/v1/auth/logout/');
    } catch (e) {
      // Ignore logout errors if session expired
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },
  getBrokerCredentials: async (): Promise<BrokerCredentialsInfo> => {
    const response = await api.get('/api/v1/auth/broker/');
    return response.data;
  },
  updateBrokerCredentials: async (data: BrokerCredentialsInfo): Promise<BrokerCredentialsInfo> => {
    const response = await api.put('/api/v1/auth/broker/', data);
    return response.data;
  },
  getPortfolioSummaryAuth: async () => {
    const response = await api.get('/api/v1/auth/portfolio/');
    return response.data;
  },
};

export default api;

