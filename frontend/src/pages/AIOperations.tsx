import { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { aiOpsApi, AIOperationsData } from '../services/api';
import { Activity, Server, Database, BrainCircuit, RefreshCw, CheckCircle2, AlertTriangle, XCircle, TerminalSquare, Clock } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function AIOperations() {
  const [data, setData] = useState<AIOperationsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await aiOpsApi.getDashboard();
      setData(res);
    } catch (err) {
      console.error("Failed to fetch AI ops data", err);
      setError("Unable to load AI Operations telemetry. Please verify backend connection.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    if (['Healthy', 'Running', 'Success', 'Active', 'Connected'].some(s => status.includes(s))) return 'text-emerald-400';
    if (['Warning', 'Idle', 'Degraded'].some(s => status.includes(s))) return 'text-amber-400';
    if (['Error', 'Offline', 'Failure'].some(s => status.includes(s))) return 'text-red-400';
    return 'text-gray-400';
  };

  const getStatusIcon = (status: string) => {
    if (['Healthy', 'Running', 'Success', 'Active', 'Connected'].some(s => status.includes(s))) return <CheckCircle2 size={16} className="text-emerald-400 mr-2" />;
    if (['Warning', 'Idle', 'Degraded'].some(s => status.includes(s))) return <AlertTriangle size={16} className="text-amber-400 mr-2" />;
    return <XCircle size={16} className="text-red-400 mr-2" />;
  };

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 space-y-4 py-20">
        <RefreshCw size={32} className="animate-spin text-blue-500" />
        <p>Connecting to AI Orchestrator...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6">
        <Card className="border-red-500/20 bg-red-500/5 text-center py-10">
          <AlertTriangle size={48} className="text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Telemetry Offline</h2>
          <p className="text-gray-400 mb-6">{error}</p>
          <Button onClick={fetchData}>Retry Connection</Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-10" id="ai-operations-page">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center">
            <Activity className="mr-3 text-blue-500" size={32} />
            AI Operations
          </h1>
          <p className="text-sm text-gray-400 mt-1">Enterprise Model Telemetry & Agent Monitoring</p>
        </div>
        <Button variant="secondary" onClick={fetchData} disabled={loading}>
          <RefreshCw size={16} className={`mr-2 ${loading ? 'animate-spin' : ''}`} /> 
          Refresh
        </Button>
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-sm text-gray-400 mb-1">Today's Requests</div>
          <div className="text-2xl font-bold text-white">{data.llm_usage.today_requests.toLocaleString()}</div>
          <div className="text-xs text-emerald-400 mt-1">Avg Latency: {data.llm_usage.avg_response_time}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-400 mb-1">Tokens Processed</div>
          <div className="text-2xl font-bold text-white">{(data.llm_usage.today_tokens / 1000000).toFixed(2)}M</div>
          <div className="text-xs text-gray-500 mt-1">{data.llm_usage.prompt_tokens.toLocaleString()} Prompt / {data.llm_usage.completion_tokens.toLocaleString()} Comp</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-400 mb-1">Cache Hit Rate</div>
          <div className="text-2xl font-bold text-white">{data.llm_usage.cache_hits}</div>
          <div className="text-xs text-amber-400 mt-1">{data.llm_usage.retry_count} Retries today</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-400 mb-1">Est. Daily Cost</div>
          <div className="text-2xl font-bold text-white">${data.llm_usage.est_daily_cost.toFixed(2)}</div>
          <div className="text-xs text-gray-500 mt-1">Projected: ${data.llm_usage.est_monthly_cost.toFixed(2)} / mo</div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Agents & Charts */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-5">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center">
              <BrainCircuit className="mr-2 text-blue-500" size={20} />
              Agent Cluster Status
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {data.agent_status.map((agent, i) => (
                <div key={i} className="bg-white/5 border border-white/10 rounded-lg p-3 flex flex-col">
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-medium text-white text-sm">{agent.name}</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full bg-white/5 ${getStatusColor(agent.status)}`}>{agent.status}</span>
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mt-auto">
                    <span>Latency: <span className="text-white">{agent.latency}</span></span>
                    <span>Success: <span className="text-white">{agent.success}</span></span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="text-lg font-bold text-white mb-4">Token Usage Analytics (7 Days)</h2>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.chart_data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                  <XAxis dataKey="date" stroke="#888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${(value / 1000)}k`} />
                  <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '0.5rem' }} itemStyle={{ color: '#e5e7eb' }} />
                  <Line type="monotone" dataKey="tokens" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} name="Tokens" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        {/* Right Column: Health & Services */}
        <div className="space-y-6">
          <Card className="p-5">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center">
              <Server className="mr-2 text-blue-500" size={20} />
              System Health
            </h2>
            <div className="space-y-3">
              {data.system_health.map((sys, i) => (
                <div key={i} className="flex items-center justify-between border-b border-white/5 pb-2 last:border-0 last:pb-0">
                  <span className="text-sm text-gray-300">{sys.service}</span>
                  <div className="flex items-center text-sm font-medium">
                    {getStatusIcon(sys.status)}
                    <span className={getStatusColor(sys.status)}>{sys.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center">
              <Database className="mr-2 text-blue-500" size={20} />
              Model & Engine Info
            </h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-gray-400">LLM Engine</span><span className="text-white">{data.model_info.gemini_model}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Vector DB</span><span className="text-white">{data.model_info.vector_db}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Framework</span><span className="text-white">LangGraph {data.model_info.langgraph_version}</span></div>
              <div className="border-t border-white/10 my-2 pt-2"></div>
              <div className="flex justify-between"><span className="text-gray-400">RLHF Status</span><span className="text-emerald-400">{data.learning_engine.rlhf_status}</span></div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}