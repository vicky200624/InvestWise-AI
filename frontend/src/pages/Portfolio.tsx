import { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { ArrowUpRight, ArrowDownRight, Plus, RefreshCw } from 'lucide-react';

const holdings = [
  { id: '1', symbol: 'AAPL', name: 'Apple Inc.', type: 'Stock', shares: 50, avgPrice: 150.00, currentPrice: 175.20, change: 16.8 },
  { id: '2', symbol: 'MSFT', name: 'Microsoft Corp.', type: 'Stock', shares: 30, avgPrice: 280.00, currentPrice: 330.50, change: 18.0 },
  { id: '3', symbol: 'TSLA', name: 'Tesla Inc.', type: 'Stock', shares: 20, avgPrice: 220.00, currentPrice: 210.00, change: -4.5 },
  { id: '4', symbol: 'VFINX', name: 'Vanguard 500 Index', type: 'Mutual Fund', shares: 120.5, avgPrice: 380.00, currentPrice: 410.20, change: 7.9 },
];

export default function Portfolio() {
  const [activeTab, setActiveTab] = useState('All');
  
  return (
    <div className="space-y-6" id="portfolio-page">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold font-heading text-white">Portfolio</h1>
          <div className="flex items-center mt-2 space-x-2 text-sm text-[var(--color-text-secondary)]">
            <span className="flex items-center"><span className="w-2 h-2 rounded-full bg-[var(--color-accent)] mr-2"></span> Broker Sync Active</span>
            <span>•</span>
            <span className="flex items-center cursor-pointer hover:text-white transition-colors"><RefreshCw size={12} className="mr-1" /> Last synced 5m ago</span>
          </div>
        </div>
        <Button id="btn-add-holding"><Plus size={16} className="mr-2" /> Add Holding</Button>
      </div>

      <div className="flex space-x-1 border-b border-[var(--color-border)] mb-6">
        {['All', 'Stocks', 'Mutual Funds', 'Gold', 'REITs'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab 
                ? 'border-[var(--color-primary)] text-[var(--color-primary-light)]' 
                : 'border-transparent text-[var(--color-text-secondary)] hover:text-white hover:border-white/30'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white/5 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] text-sm">
                <th className="px-6 py-4 font-medium">Asset</th>
                <th className="px-6 py-4 font-medium text-right">Shares</th>
                <th className="px-6 py-4 font-medium text-right">Avg. Price</th>
                <th className="px-6 py-4 font-medium text-right">Current Price</th>
                <th className="px-6 py-4 font-medium text-right">Total Value</th>
                <th className="px-6 py-4 font-medium text-right">Return</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {holdings.map((h) => {
                const isPositive = h.change >= 0;
                const totalValue = h.shares * h.currentPrice;
                return (
                  <tr key={h.id} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center font-bold text-white mr-3">
                          {h.symbol[0]}
                        </div>
                        <div>
                          <div className="font-semibold text-white">{h.symbol}</div>
                          <div className="text-xs text-[var(--color-text-secondary)]">{h.name}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right text-white">{h.shares}</td>
                    <td className="px-6 py-4 text-right text-[var(--color-text-secondary)]">${h.avgPrice.toFixed(2)}</td>
                    <td className="px-6 py-4 text-right text-white font-medium">${h.currentPrice.toFixed(2)}</td>
                    <td className="px-6 py-4 text-right text-white font-semibold">${totalValue.toFixed(2)}</td>
                    <td className="px-6 py-4 text-right">
                      <div className={`inline-flex items-center px-2.5 py-1 rounded-md text-sm font-medium ${
                        isPositive ? 'bg-[var(--color-accent)]/10 text-[var(--color-accent)]' : 'bg-[var(--color-danger)]/10 text-[var(--color-danger)]'
                      }`}>
                        {isPositive ? <ArrowUpRight size={14} className="mr-1" /> : <ArrowDownRight size={14} className="mr-1" />}
                        {Math.abs(h.change)}%
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
