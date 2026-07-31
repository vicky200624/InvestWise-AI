import { useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import { ScoreGauge } from '../components/ui/ScoreGauge';
import { PortfolioDonut } from '../components/charts/PortfolioDonut';
import { PerformanceLine } from '../components/charts/PerformanceLine';
import { TrendingUp, Activity, Zap } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { useNavigate } from 'react-router-dom';
import { portfolioApi, DashboardSummary } from '../services/api';

const DEFAULT_SUMMARY: DashboardSummary = {
  total_invested: 110000,
  current_value: 124563,
  overall_score: 84,
  xirr: 13.24,
  last_synced: '2026-07-31T10:00:00Z',
  allocation: [
    { name: 'Stocks', value: 65 },
    { name: 'Mutual Funds', value: 20 },
    { name: 'Gold', value: 10 },
    { name: 'REITs', value: 5 },
  ],
  performance: [
    { month: 'Jan', return: 2.1 },
    { month: 'Feb', return: 1.8 },
    { month: 'Mar', return: 3.4 },
    { month: 'Apr', return: -0.5 },
    { month: 'May', return: 4.2 },
    { month: 'Jun', return: 2.2 },
  ],
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<DashboardSummary>(DEFAULT_SUMMARY);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    const fetchSummary = async () => {
      try {
        const data = await portfolioApi.getDashboardSummary();
        if (isMounted && data) {
          setSummary(data);
        }
      } catch (error) {
        // Fallback to default summary if backend offline or unauthenticated
        console.warn('Failed to fetch dashboard summary, using fallback data:', error);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchSummary();
    return () => {
      isMounted = false;
    };
  }, []);

  const gain = summary.current_value - summary.total_invested;
  const gainPct = summary.total_invested > 0 ? (gain / summary.total_invested) * 100 : 0;

  return (
    <div className="space-y-6" id="dashboard-page">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold font-heading text-white">Dashboard</h1>
          <p className="text-[var(--color-text-secondary)]">
            {loading ? 'Updating your portfolio overview...' : "Welcome back! Here's your portfolio overview."}
          </p>
        </div>
        <div className="flex space-x-3">
          <Button id="btn-optimize-portfolio" variant="secondary" onClick={() => navigate('/portfolio')}>
            <Activity className="w-4 h-4 mr-2" /> Optimize Portfolio
          </Button>
          <Button id="btn-analyze-stock" onClick={() => navigate('/research')}>
            <Zap className="w-4 h-4 mr-2" /> Analyze Stock
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card hoverEffect className="col-span-1 md:col-span-2 relative overflow-hidden flex flex-col justify-between p-8">
          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-[var(--color-primary)]/20 to-[var(--color-accent)]/10 rounded-full blur-3xl -z-10 transform translate-x-1/3 -translate-y-1/3" />
          <div>
            <p className="text-[var(--color-text-secondary)] font-medium mb-1">Total Portfolio Value</p>
            <h2 className="text-5xl font-bold font-heading text-white tracking-tight">
              ${summary.current_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </h2>
            <div className="flex items-center mt-3 text-[var(--color-accent)] bg-[var(--color-accent)]/10 px-3 py-1 rounded-full w-fit">
              <TrendingUp size={16} className="mr-1" />
              <span className="text-sm font-medium">
                {gain >= 0 ? '+' : ''}
                {gainPct.toFixed(1)}% (${gain.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}) All time
              </span>
            </div>
          </div>
        </Card>

        <Card hoverEffect className="flex flex-col items-center justify-center py-8">
          <h3 className="text-lg font-medium text-white mb-4">Health Score</h3>
          <ScoreGauge score={Math.round(summary.overall_score)} size={140} />
          <p className="text-sm text-[var(--color-text-secondary)] mt-4 text-center px-4">
            {summary.overall_score >= 70
              ? 'Your portfolio is well diversified and performing optimally.'
              : 'Your portfolio needs rebalancing to reduce sector concentration risk.'}
          </p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-medium text-white">Performance (30 Days)</h3>
            <button
              onClick={() => navigate('/portfolio')}
              className="text-[var(--color-primary-light)] text-sm hover:underline cursor-pointer"
            >
              View Details
            </button>
          </div>
          <PerformanceLine data={summary.performance} />
        </Card>
        
        <Card>
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-medium text-white">Asset Allocation</h3>
          </div>
          <div className="flex items-center">
            <div className="w-1/2">
              <PortfolioDonut data={summary.allocation} />
            </div>
            <div className="w-1/2 pl-4 space-y-4">
              {summary.allocation.map((item, index) => {
                const colors = ['bg-purple-500', 'bg-emerald-400', 'bg-amber-500', 'bg-red-500', 'bg-blue-500'];
                const color = colors[index % colors.length];
                return (
                  <div key={item.name} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className={`w-3 h-3 rounded-full ${color} mr-3`} />
                      <span className="text-sm text-gray-300">{item.name}</span>
                    </div>
                    <span className="text-sm font-semibold text-white">{item.value}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
