import React from 'react';
import { CheckCircle2, Clock, Loader2, ArrowRight, AlertTriangle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

interface WorkflowExecutionProps {
  workflowId: string;
  onBack: () => void;
  onComplete: () => void;
}

interface Agent {
  id: string;
  name: string;
  desc: string;
}

interface Task {
  id: number;
  name: string;
  status: string;
  progress: string;
  time: string;
}

interface ExecutionData {
  agents: Agent[];
  tasks: Task[];
  isFinished: boolean;
}

const fetchExecutionConfig = async (workflowId: string): Promise<ExecutionData> => {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`http://localhost:8000/api/agentic-direct/execution/${workflowId}/`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'x-api-version': '1.0'
    }
  });
  
  if (!response.ok) {
    throw new Error(`Execution fetch failed with status ${response.status}`);
  }
  
  const data = await response.json();
  
  // Determine if workflow is completely finished based on real backend task states
  const allTasksCompleted = data.tasks?.length > 0 && data.tasks.every((t: Task) => t.status === 'Completed' || t.status === 'Success');
  
  return {
    agents: data.agents || [],
    tasks: data.tasks || [],
    isFinished: allTasksCompleted
  };
};

export default function WorkflowExecution({ workflowId, onBack, onComplete }: WorkflowExecutionProps) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['agenticExecution', workflowId],
    queryFn: () => fetchExecutionConfig(workflowId),
    refetchInterval: (query) => (query.state.data?.isFinished ? false : 15000), // Auto-refresh every 15s if not finished
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <Loader2 size={48} className="text-blue-500 animate-spin" />
        <h3 className="text-xl font-bold text-white">Connecting to LangGraph Orchestrator...</h3>
        <p className="text-gray-400 text-sm">Fetching real-time execution state</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <AlertTriangle size={48} className="text-red-500" />
        <h3 className="text-xl font-bold text-white">Failed to load execution pipeline</h3>
        <p className="text-red-400 text-sm">{error instanceof Error ? error.message : 'Unknown error occurred'}</p>
        <button onClick={onBack} className="mt-4 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors">Go Back</button>
      </div>
    );
  }

  const agents = data?.agents || [];
  const tasks = data?.tasks || [];
  const isFinished = data?.isFinished || false;

  return (
    <div className="space-y-8 pb-10" id="workflow-execution">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Multi-Agent Orchestration</h2>
          <p className="text-sm text-gray-400">Executing workflow: <span className="text-blue-400 capitalize">{workflowId.replace('_', ' ')}</span></p>
        </div>
        <button 
          onClick={onBack}
          className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg transition-colors border border-white/10 text-sm"
        >
          Cancel / Back
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left 2 Cols: Live Agent Pipeline */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-6 flex items-center">
              Agent Execution Pipeline
              {!isFinished && <Loader2 size={16} className="ml-3 text-blue-400 animate-spin" />}
            </h3>
            
            <div className="space-y-4">
              {agents.length === 0 ? (
                 // Skeleton Loader
                 [1, 2, 3].map(i => (
                   <div key={i} className="animate-pulse flex items-center p-4 rounded-lg bg-white/5 border border-white/5">
                      <div className="h-10 w-10 bg-white/10 rounded-lg mr-4"></div>
                      <div className="flex-1 space-y-2">
                         <div className="h-4 w-1/3 bg-white/10 rounded"></div>
                         <div className="h-3 w-1/2 bg-white/10 rounded"></div>
                      </div>
                   </div>
                 ))
              ) : (
                agents.map((agent) => {
                  // Map dynamic agent status to LangGraph task progression
                  const activeTask = tasks.find(t => t.status === 'Running' || t.status === 'In Progress');
                  
                  let status = 'Waiting';
                  let statusColor = 'text-gray-400 bg-gray-500/10 border-gray-500/20';
                  let icon = <Clock size={16} className="text-gray-400" />;
                  
                  const agentIndex = agents.findIndex(a => a.id === agent.id);
                  const runningIndex = activeTask ? Math.min(agents.length - 1, tasks.findIndex(t => t.id === activeTask.id)) : agents.length;
                  
                  if (agentIndex < runningIndex || isFinished) {
                    status = 'Completed';
                    statusColor = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
                    icon = <CheckCircle2 size={16} className="text-emerald-400" />;
                  } else if (agentIndex === runningIndex && !isFinished) {
                    status = 'Running';
                    statusColor = 'text-blue-400 bg-blue-500/10 border-blue-500/20 animate-pulse';
                    icon = <Loader2 size={16} className="text-blue-400 animate-spin" />;
                  }

                  return (
                    <div key={agent.id} className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/5">
                      <div className="flex items-center space-x-4">
                        <div className={`p-2 rounded-lg border ${statusColor}`}>
                          {icon}
                        </div>
                        <div>
                          <h4 className="font-semibold text-white text-sm">{agent.name}</h4>
                          <p className="text-xs text-gray-400">{agent.desc}</p>
                        </div>
                      </div>

                      <div className="text-right">
                        <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${statusColor}`}>
                          {status}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {isFinished && (
              <div className="mt-6 pt-6 border-t border-[var(--color-border)] flex justify-end">
                <button
                  onClick={onComplete}
                  className="flex items-center px-6 py-3 bg-[var(--color-primary)] hover:bg-blue-600 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/20"
                >
                  View Final Results & Analysis
                  <ArrowRight size={18} className="ml-2" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Task Queue & Telemetry */}
        <div className="space-y-6">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4">Live Task Queue</h3>
            
            <div className="space-y-3">
              {tasks.length === 0 ? (
                // Skeleton Loader
                [1, 2, 3, 4].map(i => (
                  <div key={i} className="animate-pulse p-3 bg-white/5 border border-white/10 rounded-lg space-y-2">
                     <div className="flex justify-between">
                        <div className="h-4 w-1/2 bg-white/10 rounded"></div>
                        <div className="h-4 w-12 bg-white/10 rounded"></div>
                     </div>
                     <div className="flex justify-between mt-2">
                        <div className="h-3 w-1/4 bg-white/10 rounded"></div>
                        <div className="h-3 w-1/4 bg-white/10 rounded"></div>
                     </div>
                  </div>
                ))
              ) : (
                tasks.map((task) => (
                  <div key={task.id} className="p-3 bg-white/5 border border-white/10 rounded-lg space-y-2">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-white font-medium">{task.name}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        task.status === 'Completed' || task.status === 'Success' ? 'bg-emerald-500/10 text-emerald-400' :
                        task.status === 'Running' ? 'bg-blue-500/10 text-blue-400 animate-pulse' : 
                        task.status === 'Failed' ? 'bg-red-500/10 text-red-400' :
                        'bg-gray-500/10 text-gray-400'
                      }`}>
                        {task.status}
                      </span>
                    </div>
                    <div className="flex justify-between text-xs text-gray-400">
                      <span>Progress: {task.progress}</span>
                      <span>{task.time}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}