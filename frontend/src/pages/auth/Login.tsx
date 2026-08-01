import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage('');

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      if (err.response?.status === 401) {
        setErrorMessage('Invalid email or password.');
      } else if (err.response?.status === 409) {
        setErrorMessage('Account exists with a different method. Try resetting your password.');
      } else {
        setErrorMessage(err.response?.data?.detail || 'Login failed. Please check server connection.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--color-bg-base)] flex items-center justify-center relative overflow-hidden" id="login-page">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[var(--color-primary)]/20 rounded-full blur-[100px]" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[var(--color-accent)]/20 rounded-full blur-[100px]" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md z-10"
      >
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-[var(--color-primary)] to-[var(--color-accent)] mx-auto mb-6 shadow-xl shadow-primary/20 rotate-12 flex items-center justify-center">
            <div className="w-8 h-8 bg-white/20 rounded-lg -rotate-12 backdrop-blur-sm" />
          </div>
          <h1 className="text-4xl font-bold font-heading text-white tracking-tight">InvestWise-AI</h1>
          <p className="text-[var(--color-text-secondary)] mt-2">Sign in to your intelligent portfolio</p>
        </div>

        <Card className="p-8 border border-white/10 bg-white/5 backdrop-blur-2xl">
          {errorMessage && (
            <div className="mb-4 p-3 rounded-lg bg-red-500/20 border border-red-500/30 text-red-300 text-sm text-center">
              {errorMessage}
            </div>
          )}
          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5" htmlFor="email">Email</label>
              <input
                id="email"
                type="text"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-black/20 border border-white/10 rounded-xl focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] text-white transition-all"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="block text-sm font-medium text-gray-300" htmlFor="password">Password</label>
                <a href="#" className="text-xs text-[var(--color-primary-light)] hover:underline">Forgot password?</a>
              </div>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-black/20 border border-white/10 rounded-xl focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] text-white transition-all"
                placeholder="••••••••"
              />
            </div>

            <Button type="submit" className="w-full py-3 mt-4" isLoading={isLoading} id="btn-login-submit">
              Sign In
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-[var(--color-text-secondary)]">
            Don't have an account? <Link to="/register" className="text-white font-medium hover:underline">Create one</Link>
          </div>
        </Card>
      </motion.div>
    </div>
  );
}