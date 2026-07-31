import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { motion } from 'framer-motion';

export default function Login() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      navigate('/dashboard');
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-[var(--color-bg-base)] flex items-center justify-center relative overflow-hidden" id="login-page">
      {/* Animated background elements */}
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
          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5" htmlFor="email">Email Address</label>
              <input 
                id="email" 
                type="email" 
                required 
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
                className="w-full px-4 py-3 bg-black/20 border border-white/10 rounded-xl focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] text-white transition-all" 
                placeholder="••••••••"
              />
            </div>
            
            <Button type="submit" className="w-full py-3 mt-4" isLoading={isLoading} id="btn-login-submit">
              Sign In
            </Button>
          </form>
          
          <div className="mt-6 text-center text-sm text-[var(--color-text-secondary)]">
            Don't have an account? <a href="#" className="text-white font-medium hover:underline">Create one</a>
          </div>
        </Card>
      </motion.div>
    </div>
  );
}
