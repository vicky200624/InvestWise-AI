import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg-base)]">
                    <div className="max-w-md w-full mx-auto p-8">
                        <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-6">
                            <h2 className="text-2xl font-bold text-red-400 mb-4">Something went wrong</h2>
                            <p className="text-gray-300 mb-4">
                                We're sorry, but something unexpected happened. Please try refreshing the page.
                            </p>
                            <button
                                onClick={() => this.setState({ hasError: false, error: null })}
                                className="w-full bg-red-500 hover:bg-red-600 text-white font-medium py-3 px-4 rounded-xl transition-colors"
                            >
                                Try Again
                            </button>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;