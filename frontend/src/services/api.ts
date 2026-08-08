import axios from 'axios';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || (import.meta as any).env?.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Version': '1.0',
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

// Queue mechanism for handling concurrent requests during token refresh
let isRefreshing = false;
let failedQueue: Array<{ resolve: (value?: unknown) => void; reject: (reason?: any) => void }> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response interceptor for error handling and automatic JWT refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      
      if (isRefreshing) {
        // If a refresh is already in progress, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return api(originalRequest);
        }).catch(err => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');
      
      if (refreshToken) {
        try {
          // Use standard axios to avoid triggering interceptors recursively
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

          // Process all queued requests with the new token
          processQueue(null, newAccessToken);
          
          return api(originalRequest);
        } catch (refreshError) {
          // If refresh fails, clear auth state and reject queued requests
          processQueue(refreshError, null);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login'; // Optional: Redirect to login
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      } else {
        // No refresh token available, clear whatever is left
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
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
    const response = await api.post('/api/v1/portfolio/sync-broker/');
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
    if (Array.isArray(response.data)) {
      return response.data;
    }
    return response.data?.results || [];
  },
  
  getItems: async () => {
    const response = await api.get('/api/watchlist/items/');
    if (Array.isArray(response.data)) {
      return response.data;
    }
    return response.data?.results || [];
  },
  
  addItem: async (symbol: string, targetPrice?: number) => {
    // 1. Fetch the user's actual watchlists
    const wListResponse = await api.get('/api/watchlist/');
    const watchlists = Array.isArray(wListResponse.data) 
      ? wListResponse.data 
      : (wListResponse.data?.results || []);
    
    let validWatchlistId;
    
    // 2. If the user doesn't have a watchlist yet, create one on the fly
    if (watchlists.length === 0) {
      const newWl = await api.post('/api/watchlist/', { name: 'Main Watchlist' });
      validWatchlistId = newWl.data.id;
    } else {
      // Otherwise, use the ID of their first watchlist
      validWatchlistId = watchlists[0].id;
    }

    // 3. Post the new item using the verified valid Watchlist ID
    const response = await api.post('/api/watchlist/items/', {
      symbol: symbol.toUpperCase(),
      target_price: targetPrice || 0,
      watchlist: validWatchlistId 
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
    // Backend CustomUser uses email as USERNAME_FIELD, so JWT expects "email"
    const response = await api.post('/api/v1/auth/login/', {
      email: usernameOrEmail,
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
  getLinkedBrokers: async (): Promise<any[]> => {
    // Just a placeholder mapping to broker credentials or list if implemented
    const response = await api.get('/api/v1/auth/broker/');
    return [response.data]; // Wrap in array as expected by frontend
  },
  linkBroker: async (data: any): Promise<any> => {
    // Backend BrokerCredentialsView is a RetrieveUpdateAPIView (GET/PUT/PATCH)
    const response = await api.put('/api/v1/auth/broker/', data);
    return response.data;
  },
  getPortfolioSummaryAuth: async () => {
    const response = await api.get('/api/v1/auth/portfolio/');
    return response.data;
  },
};

export default api;
export interface AIOperationsData {
  agent_status: Array<{ name: string; status: string; last_exec: string; latency: string; success: string; health: string }>;
  llm_usage: {
    today_requests: number;
    today_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
    est_daily_cost: number;
    est_monthly_cost: number;
    avg_response_time: string;
    cache_hits: string;
    failed_requests: number;
    retry_count: number;
  };
  model_info: Record<string, string | number>;
  learning_engine: Record<string, string>;
  background_services: Record<string, string | number>;
  recent_activity: Array<{ time: string; type: string; desc: string; status: string }>;
  chart_data: Array<{ date: string; tokens: number; latency: number; accuracy: number; cost: number }>;
  system_health: Array<{ service: string; status: string }>;
}

export const aiOpsApi = {
  getDashboard: async (): Promise<AIOperationsData> => {
    const response = await api.get('/api/v1/ai-operations/dashboard/');
    return response.data;
  },
};
