import React from 'react';
import { Clock, Cpu, Play } from 'lucide-react';

interface AgentCardProps {
  title: string;
  description: string;
  time: string;
  agentCount: number;
  onRun: () => void;
}

export default function AgentCard({ title, description, time, agentCount, onRun }: AgentCardProps) {
  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 hover:border-[var(--color-primary)]/50 hover:shadow-[0_0_15px_rgba(59,130,246,0.1)] transition-all duration-300 group flex flex-col h-full relative overflow-hidden">
      
      {/* Decorative background glow */}
      <div className="absolute -top-10 -right-10 w-32 h-32 bg-[var(--color-primary)]/5 rounded-full blur-2xl group-hover:bg-[var(--color-primary)]/10 transition-colors"></div>

      <h3 className="text-lg font-bold text-white mb-2 relative z-10">{title}</h3>
      <p className="text-sm text-[var(--color-text-secondary)] mb-6 min-h-[40px] relative z-10">{description}</p>
      
      <div className="flex items-center justify-between mt-auto relative z-10 pt-4 border-t border-[var(--color-border)]/50">
        <div className="flex flex-col space-y-1.5">
          <div className="flex items-center text-xs text-gray-500">
            <Clock size={13} className="mr-1.5" />
            Est: {time}
          </div>
          <div className="flex items-center text-xs text-gray-500">
            <Cpu size={13} className="mr-1.5" />
            {agentCount} Agents
          </div>
        </div>
        
        <button 
          onClick={onRun}
          className="flex items-center justify-center px-4 py-2 bg-[var(--color-primary)]/10 text-[var(--color-primary-light)] hover:bg-[var(--color-primary)] hover:text-white rounded-lg text-sm font-medium transition-colors border border-[var(--color-primary)]/20 hover:border-[var(--color-primary)]"
        >
          <Play size={14} className="mr-2" fill="currentColor" />
          Run AI
        </button>
      </div>
    </div>
  );
}