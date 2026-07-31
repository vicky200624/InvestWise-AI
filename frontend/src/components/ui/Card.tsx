import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';

interface CardProps extends HTMLMotionProps<"div"> {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
}

export function Card({ children, className = '', hoverEffect = false, ...props }: CardProps) {
  return (
    <motion.div 
      className={`glass-card p-6 ${className}`}
      whileHover={hoverEffect ? { y: -5, boxShadow: '0 10px 30px -10px rgba(139, 92, 246, 0.2)' } : undefined}
      {...props}
    >
      {children}
    </motion.div>
  );
}
