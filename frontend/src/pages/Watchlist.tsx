import { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { ArrowUpRight, ArrowDownRight, Plus, RefreshCw, Trash2, X } from 'lucide-react';
import { watchlistApi } from '../services/api';

export interface WatchlistItem {
  id: number;
  symbol: string;
  company_name?: string;
  name?: string;
  currentPrice?: number;
  current_price?: number;
  dayChange?: number;
  day_change?: number;
  target_price?: number;
  targetPrice?: number;
}

export default function Watchlist() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [symbol, setSymbol] = useState<string>('');
  const [targetPrice, setTargetPrice] = useState<string>('');
  const [syncing, setSyncing] = useState<boolean>(false);

  const fetchWatchlist = async () => {
    setLoading(true);
    try {
      const data = await watchlistApi.getItems();
      setItems(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch watchlist:', error);
      setItems([]);
    } finally {
      setLoading(false);
      setSyncing(false);
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const handleSync = () => {
    setSyncing(true);
    fetchWatchlist();
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol) return;

    try {
      await watchlistApi.addItem(symbol.trim().toUpperCase(), parseFloat(targetPrice) || 0);
      setShowAddModal(false);
      setSymbol('');
      setTargetPrice('');
      await fetchWatchlist();
    } catch (error) {
      console.error('Error adding watchlist item:', error);
    }
  };

  const handleRemoveItem = async (id: number) => {
    try {
      await watchlistApi.removeItem(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
    } catch (error) {
      console.error('Error deleting watchlist item:', error);
    }
  };

  return (
    <div className="space-y-6" id="watchlist-page">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold font-heading text-white">Watchlist</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mt-1">
            Monitor key assets and price alerts
          </p>
        </div>
        <div className="flex space-x-3">
          <Button variant="secondary" onClick={handleSync} disabled={syncing}>
            <RefreshCw size={16} className={`mr-2 ${syncing ? 'animate-spin' : ''}`} />
            Sync
          </Button>
          <Button onClick={() => setShowAddModal(true)}>
            <Plus size={16} className="mr-2" /> Add to Watchlist
          </Button>
        </div>
      </div>

      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white/5 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] text-sm">
                <th className="px-6 py-4 font-medium">Symbol</th>
                <th className="px-6 py-4 font-medium">Company Name</th>
                <th className="px-6 py-4 font-medium text-right">Current Price</th>
                <th className="px-6 py-4 font-medium text-right">Day Change</th>
                <th className="px-6 py-4 font-medium text-right">Target Price</th>
                <th className="px-6 py-4 font-medium text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {items.length === 0 && !loading && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-[var(--color-text-secondary)]">
                    Your watchlist is empty. Click "Add to Watchlist" to start tracking assets.
                  </td>
                </tr>
              )}
              {items.map((item, i) => {
                const currentPrice = item.currentPrice ?? item.current_price ?? 0;
                const dayChange = item.dayChange ?? item.day_change ?? 0;
                const isPositive = dayChange >= 0;
                const target = item.targetPrice ?? item.target_price ?? 0;

                return (
                  <tr key={item.id || i} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="px-6 py-4 font-bold text-white uppercase">
                      {item.symbol}
                    </td>
                    <td className="px-6 py-4 text-[var(--color-text-secondary)] text-sm">
                      {item.company_name || item.name || item.symbol}
                    </td>
                    <td className="px-6 py-4 text-right text-white font-medium">
                      ₹{currentPrice.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div
                        className={`inline-flex items-center px-2.5 py-1 rounded-md text-sm font-medium ${
                          isPositive
                            ? 'bg-[var(--color-accent)]/10 text-[var(--color-accent)]'
                            : 'bg-[var(--color-danger)]/10 text-[var(--color-danger)]'
                        }`}
                      >
                        {isPositive ? <ArrowUpRight size={14} className="mr-1" /> : <ArrowDownRight size={14} className="mr-1" />}
                        {Math.abs(dayChange).toFixed(2)}%
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right text-[var(--color-text-secondary)]">
                      {target > 0 ? `₹${target.toFixed(2)}` : '—'}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <button
                        onClick={() => handleRemoveItem(item.id)}
                        className="text-gray-400 hover:text-red-400 transition-colors p-1 cursor-pointer"
                        title="Remove from Watchlist"
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <Card className="max-w-md w-full relative">
            <button
              onClick={() => setShowAddModal(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-white cursor-pointer"
            >
              <X size={20} />
            </button>
            <h2 className="text-xl font-bold text-white mb-4">Add to Watchlist</h2>
            <form onSubmit={handleAddItem} className="space-y-4">
              <div>
                <label className="block text-sm text-[var(--color-text-secondary)] mb-1">
                  Ticker / Symbol (e.g., RELIANCE, NVDA, TCS)
                </label>
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
                <label className="block text-sm text-[var(--color-text-secondary)] mb-1">
                  Target Price (Optional)
                </label>
                <input
                  type="number"
                  step="any"
                  value={targetPrice}
                  onChange={(e) => setTargetPrice(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-[var(--color-primary)]"
                  placeholder="2500.00"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <Button variant="secondary" type="button" onClick={() => setShowAddModal(false)}>
                  Cancel
                </Button>
                <Button type="submit">Add Ticker</Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}