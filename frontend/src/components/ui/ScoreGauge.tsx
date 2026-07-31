import { motion } from 'framer-motion';

interface ScoreGaugeProps {
  score: number;
  label?: string;
  size?: number;
}

export function ScoreGauge({ score, label, size = 120 }: ScoreGaugeProps) {
  const radius = (size - 20) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  
  let color = 'var(--color-accent)'; // Green
  if (score < 40) color = 'var(--color-danger)'; // Red
  else if (score < 70) color = 'var(--color-warning)'; // Yellow

  return (
    <div className="relative flex flex-col items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="var(--color-surface-elevated)"
          strokeWidth="10"
          fill="transparent"
          strokeLinecap="round"
        />
        {/* Progress circle */}
        <motion.circle
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth="10"
          fill="transparent"
          strokeDasharray={circumference}
          strokeLinecap="round"
          className="drop-shadow-lg"
          style={{ filter: `drop-shadow(0 0 6px ${color})` }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className="text-3xl font-bold font-heading text-white">{score}</span>
        {label && <span className="text-xs text-[var(--color-text-secondary)] uppercase tracking-wider mt-1">{label}</span>}
      </div>
    </div>
  );
}
