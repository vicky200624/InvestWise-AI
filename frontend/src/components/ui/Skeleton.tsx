import React from 'react';

interface SkeletonProps {
    className?: string;
    variant?: 'text' | 'circular' | 'rectangular';
    width?: string | number;
    height?: string | number;
}

export function Skeleton({ className = '', variant = 'rectangular', width, height }: SkeletonProps) {
    const baseClasses = 'animate-pulse bg-white/10';

    const variantClasses = {
        text: 'rounded h-4',
        circular: 'rounded-full',
        rectangular: 'rounded-lg',
    };

    const style: React.CSSProperties = {
        width: width || '100%',
        height: height || (variant === 'text' ? '1rem' : '100%'),
    };

    return (
        <div
            className={`${baseClasses} ${variantClasses[variant]} ${className}`}
            style={style}
        />
    );
}

// Skeleton Card component for loading states
export function SkeletonCard() {
    return (
        <div className="glass-card p-6 space-y-4">
            <Skeleton variant="rectangular" height={120} />
            <Skeleton variant="text" width="60%" />
            <Skeleton variant="text" width="80%" />
            <div className="flex space-x-2">
                <Skeleton variant="rectangular" width={80} height={36} />
                <Skeleton variant="rectangular" width={80} height={36} />
            </div>
        </div>
    );
}

// Skeleton Table component for loading states
export function SkeletonTable({ rows = 5 }: { rows?: number }) {
    return (
        <div className="glass-card p-0 overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className="bg-white/5 border-b border-[var(--color-border)]">
                            {['Asset', 'Qty', 'Price', 'Value', 'Return'].map((header) => (
                                <th key={header} className="px-6 py-4">
                                    <Skeleton variant="text" width={80} />
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {Array.from({ length: rows }).map((_, i) => (
                            <tr key={i} className="border-b border-[var(--color-border)]">
                                {Array.from({ length: 5 }).map((_, j) => (
                                    <td key={j} className="px-6 py-4">
                                        <Skeleton variant="text" />
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
