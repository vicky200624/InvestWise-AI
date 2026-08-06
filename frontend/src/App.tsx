import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AppLayout from './components/layout/AppLayout';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './components/ui/Toast';
import Dashboard from './pages/Dashboard';
import Portfolio from './pages/Portfolio';
import Research from './pages/Research';
import Watchlist from './pages/Watchlist';
import Chat from './pages/Chat';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import ConnectBroker from './pages/ConnectBroker'; 
import ErrorBoundary from './components/ErrorBoundary';
import AIOperations from './pages/AIOperations';
import AgenticAI from './pages/AgenticAI';

// Initialize the React Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false, // Prevents unnecessary refetches when switching browser tabs
      retry: 1, // Only retry failed requests once before showing the error UI
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <ToastProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <AppLayout />
                    </ProtectedRoute>
                  }
                >
                  <Route index element={<Navigate to="/dashboard" replace />} />
                  <Route path="dashboard" element={<Dashboard />} />
                  <Route path="portfolio" element={<Portfolio />} />
                  <Route path="research" element={<Research />} />
                  <Route path="watchlist" element={<Watchlist />} />
                  <Route path="chat" element={<Chat />} />
                  <Route path="connect-broker" element={<ConnectBroker />} /> 
                  <Route path="agentic-ai" element={<AgenticAI />} />
                  <Route path="ai-operations" element={<AIOperations />} />
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Route>
              </Routes>
            </BrowserRouter>
          </ToastProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;