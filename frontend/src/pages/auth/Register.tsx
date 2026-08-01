import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';

export default function Register() {
    const navigate = useNavigate();
    const { register } = useAuth();
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setErrorMessage('');

        if (password !== confirmPassword) {
            setErrorMessage('Passwords do not match.');
            return;
        }
        if (password.length < 6) {
            setErrorMessage('Password must be at least 6 characters long.');
            return;
        }

        setIsLoading(true);
        try {
            await register(username, email, password);
            navigate('/dashboard');
        } catch (err: any) {
            if (err.response?.status === 400) {
                const detail = err.response?.data;
                if (detail?.email) {
                    setErrorMessage(`Email: ${detail.email[0] || detail.email}`);
                } else if (detail?.username) {
                    setErrorMessage(`Username: ${detail.username[0] || detail.username}`);
                } else if (detail?.password) {
                    setErrorMessage(`Password: ${detail.password[0] || detail.password}`);
                } else {
                    setErrorMessage(detail?.detail || 'Registration failed. Please check your inputs.');
                }
            } else if (err.response?.status === 409) {
                setErrorMessage('An account with this email already exists. Please log in.');
            } else {
                setErrorMessage(err.response?.data?.detail || 'Registration failed. Please check server connection.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[var(--color-bg-base)] flex items-center justify-center relative overflow-hidden" id="register-page">
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
                    <p className="text-[var(--color-text-secondary)] mt-2">Create your intelligent portfolio account</p>
                </div>

                <Card className="p-8 border border-white/10 bg-white/5 backdrop-blur-2xl">
                    {errorMessage && (
                        <div className="mb-4 p-3 rounded-lg bg-red-500/20 border border-red-500/30 text-red-300 text-sm text-center">
                            {errorMessage}
                        </div>
                    )}
                    <form onSubmit={handleRegister} className="space-y-5">
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1.5" htmlFor="username">Username</label>
                            <input
                                id="username"
                                type="text"
                                required
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full px-4 py-3 bg-black/20 border border-white/10 rounded-xl focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] text-white transition-all"
                                placeholder="johndoe"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1.5" htmlFor="email">Email</label>
                            <input
                                id="email"
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-3 bg-black/20 border border-white/10 rounded-xl focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] text-white transition-all"
                                placeholder="you@example.com"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1.5" htmlFor="password">Password</label>
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
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1.5" htmlFor="confirmPassword">Confirm Password</label>
                            <input
                                id="confirmPassword"
                                type="password"
                                required
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                className="w-full px-4 py-3 bg-black/20 border border-white/10 rounded-xl focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] text-white transition-all"
                                placeholder="••••••••"
                            />
                        </div>

                        <Button type="submit" className="w-full py-3 mt-4" isLoading={isLoading} id="btn-register-submit">
                            Create Account
                        </Button>
                    </form>

                    <div className="mt-6 text-center text-sm text-[var(--color-text-secondary)]">
                        Already have an account? <Link to="/login" className="text-white font-medium hover:underline">Sign in</Link>
                    </div>
                </Card>
            </motion.div>
        </div>
    );
}