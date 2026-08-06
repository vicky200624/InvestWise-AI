import React from 'react';
import { ArrowLeft, CheckCircle2, TrendingUp, Award, Zap, Brain, Clock, BarChart3, Loader2, AlertTriangle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

interface WorkflowResultProps {
  workflowId: string;
  onBack: () => void;
}

const fetchResults = async (workflowId: string) => {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`http://localhost:8000/api/agentic-direct/result/${workflowId}/`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'x-api-version': '1.0' // Resolves the 426 backend middleware block
    }
  });
  
  if (!response.ok) {
    throw new Error(`Results fetch failed with status ${response.status}`);
  }
  
  return response.json();
};

export default function WorkflowResult({ workflowId, onBack }: WorkflowResultProps) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['workflowResult', workflowId],
    queryFn: () => fetchResults(workflowId),
    staleTime: 5 * 60 * 1000, // Keep results cached for 5 minutes before refetching
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <Loader2 size={48} className="text-blue-500 animate-spin" />
        <h3 className="text-xl font-bold text-white">Synthesizing Final AI Results...</h3>
        <p className="text-gray-400 text-sm">Processing real portfolio metrics and financial models</p>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <AlertTriangle size={48} className="text-red-500" />
        <h3 className="text-xl font-bold text-white">Failed to load analysis results</h3>
        <p className="text-red-400 text-sm">{error instanceof Error ? error.message : 'Unknown error occurred'}</p>
        <button onClick={onBack} className="mt-4 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors">Go Back</button>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12" id="workflow-results">
      
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between bg-gradient-to-r from-blue-600/10 via-purple-600/15 to-transparent p-6 rounded-2xl border border-blue-500/20">
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-emerald-400 text-sm font-semibold">
            <CheckCircle2 size={18} />
            <span>Multi-Agent Orchestration Complete</span>
          </div>
          <h2 className="text-3xl font-bold text-white capitalize">{data.workflow_id.replace('_', ' ')}: Results & Insights</h2>
          <p className="text-sm text-gray-400">Synthesized using LangGraph intelligence engine, live market data feeds, and historical vector memory.</p>
        </div>
        <button 
          onClick={onBack}
          className="mt-4 md:mt-0 flex items-center px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-xl transition-colors border border-white/10 text-sm font-medium"
        >
          <ArrowLeft size={16} className="mr-2" />
          Run Another Workflow
        </button>
      </div>

      {/* Executive Summary & Key Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Executive Summary */}
        <div className="lg:col-span-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 space-y-4">
          <h3 className="text-lg font-bold text-white flex items-center">
            <Award className="mr-2 text-blue-400" size={20} />
            Executive Summary
          </h3>
          <p className="text-gray-300 text-sm leading-relaxed">{data.summary.text}</p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-white/5">
            <div className="bg-white/5 p-3 rounded-xl border border-white/5">
              <div className="text-xs text-gray-400">Risk Score</div>
              <div className="text-xl font-bold text-amber-400 mt-1">{data.summary.risk_score}</div>
            </div>
            <div className="bg-white/5 p-3 rounded-xl border border-white/5">
              <div className="text-xs text-gray-400">Confidence</div>
              <div className="text-xl font-bold text-emerald-400 mt-1">{data.summary.confidence}</div>
            </div>
            <div className="bg-white/5 p-3 rounded-xl border border-white/5">
              <div className="text-xs text-gray-400">Expected Return</div>
              <div className="text-xl font-bold text-blue-400 mt-1">{data.summary.expected_return}</div>
            </div>
            <div className="bg-white/5 p-3 rounded-xl border border-white/5">
              <div className="text-xs text-gray-400">Sharpe Ratio</div>
              <div className="text-xl font-bold text-purple-400 mt-1">{data.summary.sharpe_ratio}</div>
            </div>
          </div>
        </div>

        {/* AI Impact Widget */}
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 space-y-4">
          <h3 className="text-lg font-bold text-white flex items-center">
            <Zap className="mr-2 text-yellow-400" size={20} />
            AI Impact Summary
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/5">
              <span className="text-xs text-gray-400">AI Saved (Estimated)</span>
              <span className="text-sm font-bold text-emerald-400">{data.impact.saved}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/5">
              <span className="text-xs text-gray-400">Extra Return Generated</span>
              <span className="text-sm font-bold text-blue-400">{data.impact.extra_return}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/5">
              <span className="text-xs text-gray-400">Risk Reduced</span>
              <span className="text-sm font-bold text-purple-400">{data.impact.risk_reduced}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/5">
              <span className="text-xs text-gray-400">Bad Trades Prevented</span>
              <span className="text-sm font-bold text-amber-400">{data.impact.prevented}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Visual Comparison: Before vs After AI */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 space-y-6">
        <h3 className="text-lg font-bold text-white flex items-center">
          <BarChart3 className="mr-2 text-blue-500" size={20} />
          Portfolio Visual Comparison (Before vs After AI)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-xl p-5 space-y-4">
            <div className="flex justify-between items-center">
              <h4 className="font-semibold text-gray-300">Before AI Optimization</h4>
              <span className="text-xs px-2 py-0.5 rounded bg-gray-500/10 text-gray-400">Baseline</span>
            </div>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-gray-400">Portfolio Value</span><span className="text-white font-medium">{data.comparison.before.value}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Expected Return</span><span className="text-white font-medium">{data.comparison.before.return}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Risk Level</span><span className="text-amber-400 font-medium">{data.comparison.before.risk}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Diversification Score</span><span className="text-gray-300 font-medium">{data.comparison.before.diversification}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Volatility</span><span className="text-red-400 font-medium">{data.comparison.before.volatility}</span></div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-blue-600/10 to-emerald-600/10 border border-blue-500/30 rounded-xl p-5 space-y-4">
            <div className="flex justify-between items-center">
              <h4 className="font-semibold text-blue-400">After AI Optimization</h4>
              <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400">Optimized</span>
            </div>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-gray-400">Portfolio Value</span><span className="text-white font-medium">{data.comparison.after.value}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Expected Return</span><span className="text-emerald-400 font-medium">{data.comparison.after.return}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Risk Level</span><span className="text-emerald-400 font-medium">{data.comparison.after.risk}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Diversification Score</span><span className="text-emerald-400 font-medium">{data.comparison.after.diversification}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Volatility</span><span className="text-emerald-400 font-medium">{data.comparison.after.volatility}</span></div>
            </div>
          </div>
        </div>
      </div>

      {/* Actionable Recommendations */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 space-y-4">
        <h3 className="text-lg font-bold text-white flex items-center">
          <TrendingUp className="mr-2 text-emerald-400" size={20} />
          Recommended Actions
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data.actions.map((action: any, index: number) => {
            const isBuy = action.type === 'BUY';
            const isSell = action.type === 'SELL';
            return (
              <div key={index} className={`p-4 border rounded-xl space-y-2 ${isBuy ? 'bg-emerald-500/5 border-emerald-500/20' : isSell ? 'bg-red-500/5 border-red-500/20' : 'bg-blue-500/5 border-blue-500/20'}`}>
                <div className="flex justify-between items-center">
                  <span className={`font-bold ${isBuy ? 'text-emerald-400' : isSell ? 'text-red-400' : 'text-blue-400'}`}>{action.type}</span>
                  <span className="text-xs text-gray-400">Confidence: {action.confidence}</span>
                </div>
                <div className="text-white font-semibold">{action.assets}</div>
                <p className="text-xs text-gray-400">{action.reason}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Learning & Timeline Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 space-y-4">
          <h3 className="text-lg font-bold text-white flex items-center">
            <Brain className="mr-2 text-purple-400" size={20} />
            AI Learning & Adaptation
          </h3>
          <div className="space-y-3 text-sm">
            {data.learning.map((item: any, i: number) => (
              <div key={i} className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/5">
                <span className="text-gray-300">{item.metric}</span>
                <span className={`text-xs font-medium text-${item.color}-400`}>{item.status}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 space-y-4">
          <h3 className="text-lg font-bold text-white flex items-center">
            <Clock className="mr-2 text-cyan-400" size={20} />
            Execution Timeline
          </h3>
          <div className="space-y-4 relative border-l border-white/10 ml-3 pl-4">
            {data.timeline.map((step: any, i: number) => (
              <div key={i} className="relative">
                <div className={`absolute -left-[21px] top-1.5 w-2.5 h-2.5 rounded-full ${step.type === 'success' ? 'bg-emerald-400' : 'bg-blue-500'}`}></div>
                <div className="text-xs text-gray-400">{step.time}</div>
                <div className={`text-sm ${step.type === 'success' ? 'font-semibold text-emerald-400' : 'font-medium text-white'}`}>{step.event}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}