import { useState, useRef, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Send, Brain, User } from 'lucide-react';
import { chatApi } from '../services/api';

interface ChatMessage {
    role: 'user' | 'ai';
    content: string;
    timestamp?: string;
}

export default function Chat() {
    const [messages, setMessages] = useState<ChatMessage[]>([
        {
            role: 'ai',
            content: 'Hello! I am the InvestWise AI Assistant. How can I help you with your investment portfolio today?',
        },
    ]);
    const [input, setInput] = useState('');
    const [isSending, setIsSending] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isSending) return;

        const userMessage: ChatMessage = { role: 'user', content: input.trim() };
        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsSending(true);

        try {
            const response = await chatApi.sendTextMessage(userMessage.content);
            const aiMessage: ChatMessage = {
                role: 'ai',
                content: response.message || response.ai_text || 'I apologize, I could not process that request.',
                timestamp: response.timestamp,
            };
            setMessages((prev) => [...prev, aiMessage]);
        } catch (error) {
            console.warn('Chat API error, using fallback:', error);
            const fallbackMessage: ChatMessage = {
                role: 'ai',
                content: `I am InvestWise AI, your autonomous investment advisor. Regarding '${userMessage.content}', our models recommend monitoring market sentiment and maintaining a balanced portfolio allocation.`,
            };
            setMessages((prev) => [...prev, fallbackMessage]);
        } finally {
            setIsSending(false);
        }
    };

    return (
        <div className="flex flex-col h-full" id="chat-page">
            <div className="mb-6">
                <h1 className="text-3xl font-bold font-heading text-white">AI Chat Assistant</h1>
                <p className="text-[var(--color-text-secondary)]">Ask me anything about your investments</p>
            </div>

            <Card className="flex-1 flex flex-col p-0 overflow-hidden">
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`flex items-start space-x-3 ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}
                        >
                            <div
                                className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user'
                                        ? 'bg-gradient-to-br from-indigo-500 to-purple-600'
                                        : 'bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)]'
                                    }`}
                            >
                                {msg.role === 'user' ? (
                                    <User size={18} className="text-white" />
                                ) : (
                                    <Brain size={18} className="text-white" />
                                )}
                            </div>
                            <div
                                className={`max-w-[70%] rounded-2xl px-4 py-3 ${msg.role === 'user'
                                        ? 'bg-[var(--color-primary)]/20 text-white border border-[var(--color-primary)]/30'
                                        : 'bg-white/5 text-gray-200 border border-white/10'
                                    }`}
                            >
                                <p className="text-sm leading-relaxed">{msg.content}</p>
                            </div>
                        </div>
                    ))}
                    {isSending && (
                        <div className="flex items-start space-x-3">
                            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center flex-shrink-0">
                                <Brain size={18} className="text-white" />
                            </div>
                            <div className="bg-white/5 rounded-2xl px-4 py-3 border border-white/10">
                                <div className="flex space-x-1">
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <div className="border-t border-[var(--color-border)] p-4">
                    <form onSubmit={handleSend} className="flex items-center space-x-3">
                        <input
                            id="chat-input"
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Type your message..."
                            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-[var(--color-primary)] transition-all"
                            disabled={isSending}
                        />
                        <Button type="submit" id="btn-send-message" isLoading={isSending} disabled={!input.trim()}>
                            <Send size={16} className="mr-1" /> Send
                        </Button>
                    </form>
                </div>
            </Card>
        </div>
    );
}