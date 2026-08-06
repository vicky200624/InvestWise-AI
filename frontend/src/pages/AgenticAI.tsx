import React, { useState } from 'react';
import { Bot } from 'lucide-react';
import AgentCard from '../components/agentic/AgentCard';
import WorkflowExecution from '../components/agentic/WorkflowExecution';
import WorkflowResult from '../components/agentic/WorkflowResult';

const WORKFLOWS = [
  { id: 'optimize_portfolio', title: 'Optimize Portfolio', description: 'Rebalance weights and minimize risk using advanced quantitative models.', time: '45 sec', agentCount: 5 },
  { id: 'analyze_portfolio', title: 'Analyze My Portfolio', description: 'Deep dive into current holdings, risk factors, and market exposures.', time: '30 sec', agentCount: 3 },
  { id: 'build_portfolio', title: 'Build New Portfolio', description: 'Construct a fresh portfolio based on macro trends and personal goals.', time: '60 sec', agentCount: 6 },
  { id: 'daily_review', title: 'Daily AI Review', description: 'Quick checkup on overnight market news impacting your assets.', time: '15 sec', agentCount: 2 },
  { id: 'weekly_review', title: 'Weekly AI Review', description: 'Comprehensive weekly performance and macro-economic summary.', time: '40 sec', agentCount: 4 },
  { id: 'find_stocks', title: 'Find Best Stocks', description: 'Scan the market for undervalued assets with high momentum.', time: '50 sec', agentCount: 4 },
  { id: 'reduce_risk', title: 'Reduce Risk', description: 'Identify and automatically hedge against concentrated portfolio risks.', time: '35 sec', agentCount: 3 },
  { id: 'long_term', title: 'Find Long-Term Investments', description: 'Discover fundamentally strong companies for 5+ year holds.', time: '45 sec', agentCount: 4 },
  { id: 'dividend', title: 'Find Dividend Stocks', description: 'Screen for sustainable, high-yield dividend opportunities.', time: '30 sec', agentCount: 3 },
  { id: 'retirement', title: 'Retirement Planning', description: 'Project long-term growth and adjust for target retirement dates.', time: '55 sec', agentCount: 5 },
];

export default function AgenticAI() {
  const [activeWorkflow, setActiveWorkflow] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'execution' | 'result'>('grid');

  const handleRunWorkflow = (id: string) => {
    setActiveWorkflow(id);
    setViewMode('execution');
  };

  if (viewMode === 'execution') {
    return (
      <WorkflowExecution
        workflowId={activeWorkflow || 'optimize_portfolio'}
        onBack={() => setViewMode('grid')}
        onComplete={() => setViewMode('result')}
      />
    );
  }

  if (viewMode === 'result') {
    return (
      <WorkflowResult
        workflowId={activeWorkflow || 'optimize_portfolio'}
        onBack={() => setViewMode('grid')}
      />
    );
  }

  return (
    <div className="space-y-8 pb-10" id="agentic-ai-page">
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold text-white flex items-center">
          <Bot className="mr-3 text-[var(--color-primary-light)]" size={32} />
          Agentic AI Assistant
        </h1>
        <p className="text-sm text-[var(--color-text-secondary)]">
          What would you like AI to do? Select a workflow below to orchestrate a multi-agent system.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {WORKFLOWS.map((workflow) => (
          <AgentCard
            key={workflow.id}
            title={workflow.title}
            description={workflow.description}
            time={workflow.time}
            agentCount={workflow.agentCount}
            onRun={() => handleRunWorkflow(workflow.id)}
          />
        ))}
      </div>
    </div>
  );
}