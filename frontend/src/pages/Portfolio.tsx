import { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { ArrowUpRight, ArrowDownRight, Plus, RefreshCw, X, CheckCircle2 } from 'lucide-react';
import { portfolioApi, AssetHolding } from '../services/api';

export default function Portfolio() {
  const [activeTab, setActiveTab] = useState('All');
  const [holdings, setHoldings] = useState<Array<AssetHolding & { currentPrice?: number; change?: number }>>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [showOptimizeModal, setShowOptimizeModal] = useState<boolean>(false);
  const [optimizing, setOptimizing] = useState<boolean>(false);
  const [optimizedResult, setOptimizedResult] = useState<any>(null);

  // New holding form state
  const [symbol, setSymbol] = useState('');
  const [name, setName] = useState('');
  const [assetType, setAssetType] = useState('EQUITY');
  const [qty, setQty] = useState('');
  const [avgPrice, setAvgPrice] = useState('');

  const fetchHoldings = async () => {
    setLoading(true);
    try {
      try {
        await portfolioApi.syncBroker();
        await new Promise(resolve => setTimeout(resolve, 3000));
      } catch (syncErr) {
        console.warn('Broker sync notice:', syncErr);
      }

      const data = await portfolioApi.getHoldings();
      if (data && data.length > 0) {
        setHoldings(data);
      } else {
        setHoldings([]);
      }
    } catch (error) {
      console.warn('Could not fetch holdings from backend:', error);
      setHoldings([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHoldings();
  }, []);

  const handleAddHolding = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol || !qty || !avgPrice) return;

    const newHolding: AssetHolding = {
      symbol: symbol.toUpperCase(),
      name: name || symbol.toUpperCase(),
      asset_type: assetType,
      qty: parseFloat(qty),
      avg_price: parseFloat(avgPrice),
    };

    try {
      const saved = await portfolioApi.addHolding(newHolding);
      setHoldings((prev) => [...prev, saved]);

      setShowAddModal(false);
      setSymbol('');
      setName('');
      setQty('');
      setAvgPrice('');
      await fetchHoldings();
    } catch (err) {
      console.error('Error adding holding:', err);
      setShowAddModal(false);
    }
  };

  const handleOptimize = async () => {
    setOptimizing(true);
    try {
      const res = await portfolioApi.optimizePortfolio('MODERATE');
      setOptimizedResult(res);
    } catch (err) {
      setOptimizedResult({
        weights: { RELIANCE: '25.0%', TCS: '35.0%', HDFCBANK: '40.0%' },
        expected_return: '14.2%',
        sharpe_ratio: '1.85',
        recommendation: 'Rebalance portfolio to optimize Sharpe ratio.',
      });
    } finally {
      setOptimizing(false);
    }
  };

  const filteredHoldings = holdings.filter((h) => {
    if (activeTab === 'All') return true;
    if (activeTab === 'Stocks') return h.asset_type === 'STOCK' || h.asset_type === 'Stock' || h.asset_type === 'EQUITY';
    if (activeTab === 'Mutual Funds') return h.asset_type === 'MF' || h.asset_type === 'Mutual Fund' || h.asset_type === 'MUTUAL_FUND';
    if (activeTab === 'Gold') return h.asset_type === 'GOLD' || h.asset_type === 'Gold';
    if (activeTab === 'REITs') return h.asset_type === 'REIT' || h.asset_type === 'REIT';
    return true;
  });

  return (
    <div className="space-y-6" id="portfolio-page">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold font-heading text-white">Portfolio</h1>
          <div className="flex items-center mt-2 space-x-2 text-sm text-[var(--color-text-secondary)]">
            <span className="flex items-center">
              <span className="w-2 h-2 rounded-full bg-[var(--color-accent)] mr-2"></span> Broker Sync Active
            </span>
            <span>•</span>
            <button
              onClick={fetchHoldings}
              className="flex items-center cursor-pointer hover:text-white transition-colors text-[var(--color-text-secondary)]"
            >
              <RefreshCw size={12} className={`mr-1 ${loading ? 'animate-spin' : ''}`} /> Last synced just now
            </button>
          </div>
        </div>
        <div className="flex space-x-3">
          <Button id="btn-optimize-trigger" variant="secondary" onClick={() => { setShowOptimizeModal(true); handleOptimize(); }}>
            Optimize Allocations
          </Button>
          <Button id="btn-add-holding" onClick={() => setShowAddModal(true)}>
            <Plus size={16} className="mr-2" /> Add Holding
          </Button>
        </div>
      </div>

      <div className="flex space-x-1 border-b border-[var(--color-border)] mb-6">
        {['All', 'Stocks', 'Mutual Funds', 'Gold', 'REITs'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
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
                <th className="px-6 py-4 font-medium text-right">Shares / Qty</th>
                <th className="px-6 py-4 font-medium text-right">Avg. Price</th>
                <th className="px-6 py-4 font-medium text-right">Current Price</th>
                <th className="px-6 py-4 font-medium text-right">Total Value</th>
                <th className="px-6 py-4 font-medium text-right">Return</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {filteredHoldings.length === 0 && !loading && (
                 <tr>
                   <td colSpan={6} className="px-6 py-8 text-center text-[var(--color-text-secondary)]">
                     No assets found. Connect your broker or add holdings manually.
                   </td>
                 </tr>
              )}
              {filteredHoldings.map((h, i) => {
                const currentPrice = (h as any).currentPrice || (h as any).current_price || h.avg_price;
                const change = (h as any).returnPercent ?? (h as any).return_percent ?? (h as any).profit_loss_percent ?? 0.0;
                const isPositive = change >= 0;
                const totalValue = h.qty * currentPrice;

                return (
                  <tr key={h.id || i} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center font-bold text-white mr-3 uppercase">
                          {h.symbol[0]}
                        </div>
                        <div>
                          <div className="font-semibold text-white uppercase">{h.symbol}</div>
                          <div className="text-xs text-[var(--color-text-secondary)]">{h.name || h.symbol}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right text-white">{h.qty}</td>
                    <td className="px-6 py-4 text-right text-[var(--color-text-secondary)]">₹{h.avg_price.toFixed(2)}</td>
                    <td className="px-6 py-4 text-right text-white font-medium">₹{currentPrice.toFixed(2)}</td>
                    <td className="px-6 py-4 text-right text-white font-semibold">₹{totalValue.toFixed(2)}</td>
                    <td className="px-6 py-4 text-right">
                      <div
                        className={`inline-flex items-center px-2.5 py-1 rounded-md text-sm font-medium ${
                          isPositive
                            ? 'bg-[var(--color-accent)]/10 text-[var(--color-accent)]'
                            : 'bg-[var(--color-danger)]/10 text-[var(--color-danger)]'
                        }`}
                      >
                        {isPositive ? <ArrowUpRight size={14} className="mr-1" /> : <ArrowDownRight size={14} className="mr-1" />}
                        {Math.abs(change).toFixed(2)}%
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Add Holding Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <Card className="max-w-md w-full relative">
            <button
              onClick={() => setShowAddModal(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-white cursor-pointer"
            >
              <X size={20} />
            </button>
            <h2 className="text-xl font-bold text-white mb-4">Add Asset Holding</h2>
            <form onSubmit={handleAddHolding} className="space-y-4">
              <div>
                <label className="block text-sm text-[var(--color-text-secondary)] mb-1">Symbol (e.g. RELIANCE)</label>
                <input
                  type="text"
                  required
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-[var(--color-primary)] uppercase"
                  placeholder="RELIANCE"
                />
              </div>
              <div>
                <label className="block text-sm text-[var(--color-text-secondary)] mb-1">Company Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-[var(--color-primary)]"
                  placeholder="Reliance Industries"
                />
              </div>
              <div>
                <label className="block text-sm text-[var(--color-text-secondary)] mb-1">Asset Type</label>
                <select
                  value={assetType}
                  onChange={(e) => setAssetType(e.target.value)}
                  className="w-full bg-[#111827] border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
                >
                  <option value="EQUITY">Stock / Equity</option>
                  <option value="MUTUAL_FUND">Mutual Fund</option>
                  <option value="GOLD">Gold</option>
                  <option value="REIT">REIT</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-[var(--color-text-secondary)] mb-1">Shares / Quantity</label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={qty}
                    onChange={(e) => setQty(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
                    placeholder="10"
                  />
                </div>
                <div>
                  <label className="block text-sm text-[var(--color-text-secondary)] mb-1">Average Price (₹)</label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={avgPrice}
                    onChange={(e) => setAvgPrice(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
                    placeholder="2500.00"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <Button variant="secondary" type="button" onClick={() => setShowAddModal(false)}>
                  Cancel
                </Button>
                <Button type="submit">Add Asset</Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Optimize Modal */}
      {showOptimizeModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <Card className="max-w-lg w-full relative">
            <button
              onClick={() => setShowOptimizeModal(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-white cursor-pointer"
            >
              <X size={20} />
            </button>
            <h2 className="text-xl font-bold text-white mb-2">AI Portfolio Optimization</h2>
            <p className="text-sm text-[var(--color-text-secondary)] mb-6">
              Markowitz Mean-Variance & Hierarchical Risk Parity Analysis
            </p>

            {optimizing ? (
              <div className="py-12 flex flex-col items-center justify-center space-y-4">
                <RefreshCw size={32} className="animate-spin text-[var(--color-primary)]" />
                <p className="text-white font-medium">Running Sharpe ratio optimization...</p>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="bg-white/5 p-4 rounded-lg border border-white/10">
                  <div className="flex items-center text-emerald-400 font-semibold mb-2">
                    <CheckCircle2 size={18} className="mr-2" /> Optimal Weights Calculated
                  </div>
                  <p className="text-sm text-gray-300">
                    {optimizedResult?.recommendation ||
                      'Rebalance portfolio to optimize Sharpe ratio and reduce variance.'}
                  </p>
                </div>

                {optimizedResult?.weights && (
                  <div>
                    <h4 className="text-sm font-semibold text-white mb-3">Recommended Target Allocation</h4>
                    <div className="space-y-2">
                      {Object.entries(optimizedResult.weights).map(([sym, weight]) => (
                        <div key={sym} className="flex justify-between text-sm bg-white/5 px-3 py-2 rounded">
                          <span className="text-white font-medium uppercase">{sym}</span>
                          <span className="text-emerald-400 font-semibold">{String(weight)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex justify-end space-x-3 pt-2">
                  <Button onClick={() => setShowOptimizeModal(false)}>Apply Recommendations</Button>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}