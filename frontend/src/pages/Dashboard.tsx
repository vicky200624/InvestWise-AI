import { motion } from 'framer-motion';
import { Card } from '../components/ui/Card';
import { ScoreGauge } from '../components/ui/ScoreGauge';
import { PortfolioDonut } from '../components/charts/PortfolioDonut';
import { PerformanceLine } from '../components/charts/PerformanceLine';
import { ArrowUpRight, TrendingUp, Activity, Zap } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="space-y-6" id="dashboard-page">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold font-heading text-white">Dashboard</h1>
          <p className="text-[var(--color-text-secondary)]">Welcome back! Here's your portfolio overview.</p>
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
            <h2 className="text-5xl font-bold font-heading text-white tracking-tight">$124,563.00</h2>
            <div className="flex items-center mt-3 text-[var(--color-accent)] bg-[var(--color-accent)]/10 px-3 py-1 rounded-full w-fit">
              <TrendingUp size={16} className="mr-1" />
              <span className="text-sm font-medium">+12.5% ($13,840) All time</span>
            </div>
          </div>
        </Card>

        <Card hoverEffect className="flex flex-col items-center justify-center py-8">
          <h3 className="text-lg font-medium text-white mb-4">Health Score</h3>
          <ScoreGauge score={84} size={140} />
          <p className="text-sm text-[var(--color-text-secondary)] mt-4 text-center px-4">Your portfolio is well diversified and performing optimally.</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-medium text-white">Performance (30 Days)</h3>
            <button className="text-[var(--color-primary-light)] text-sm hover:underline">View Details</button>
          </div>
          <PerformanceLine />
        </Card>
        
        <Card>
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-medium text-white">Asset Allocation</h3>
          </div>
          <div className="flex items-center">
            <div className="w-1/2">
              <PortfolioDonut />
            </div>
            <div className="w-1/2 pl-4 space-y-4">
              {[
                { label: 'Stocks', value: '65%', color: 'bg-purple-500' },
                { label: 'Mutual Funds', value: '20%', color: 'bg-emerald-400' },
                { label: 'Gold', value: '10%', color: 'bg-amber-500' },
                { label: 'REITs', value: '5%', color: 'bg-red-500' },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full ${item.color} mr-3`} />
                    <span className="text-sm text-gray-300">{item.label}</span>
                  </div>
                  <span className="text-sm font-semibold text-white">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
