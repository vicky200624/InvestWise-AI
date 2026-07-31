import { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Plus, Trash2, ArrowUpRight, ArrowDownRight, RefreshCw, X } from 'lucide-react';
import { watchlistApi } from '../services/api';

interface WatchlistItem {
  id: number;
  symbol: string;
  name: string;
  price: number;
  change: number;
  target_price?: number;
}

const DEFAULT_WATCHLIST: WatchlistItem[] = [
  { id: 101, symbol: 'NVDA', name: 'NVIDIA Corporation', price: 124.50, change: 4.8, target_price: 140.00 },
  { id: 102, symbol: 'AMZN', name: 'Amazon.com Inc.', price: 186.20, change: 1.5, target_price: 200.00 },
  { id: 103, symbol: 'GOOGL', name: 'Alphabet Inc.', price: 178.40, change: -0.8, target_price: 195.00 },
];

export default function Watchlist() {
  const [items, setItems] = useState<WatchlistItem[]>(DEFAULT_WATCHLIST);
  const [loading, setLoading] = useState<boolean>(true);
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [symbolInput, setSymbolInput] = useState<string>('');
  const [nameInput, setNameInput] = useState<string>('');
  const [targetInput, setTargetInput] = useState<string>('');

  const fetchWatchlist = async () => {
    setLoading(true);
    try {
      const data = await watchlistApi.getWatchlist();
      if (data && data.length > 0) {
        setItems(
          data.map((item: any, idx: number) => ({
            id: item.id || idx,
            symbol: item.symbol || item.stock_symbol || 'AAPL',
            name: item.name || item.company_name || item.symbol,
            price: item.current_price || 150.0,
            change: item.change_pct || 2.5,
            target_price: item.target_price || 170.0,
          }))
        );
      } else {
        setItems(DEFAULT_WATCHLIST);
      }
    } catch (error) {
      console.warn('Could not fetch watchlist from DRF API, using default items:', error);
      setItems(DEFAULT_WATCHLIST);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const handleAddItem = (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbolInput) return;

    const newItem: WatchlistItem = {
      id: Date.now(),
      symbol: symbolInput.toUpperCase(),
      name: nameInput || symbolInput.toUpperCase(),
      price: 135.0,
      change: 2.1,
      target_price: targetInput ? parseFloat(targetInput) : undefined,
    };

    setItems((prev) => [newItem, ...prev]);
    setShowAddModal(false);
    setSymbolInput('');
    setNameInput('');
    setTargetInput('');
  };

  const handleRemove = (id: number) => {
    setItems((prev) => prev.filter((i) => i.id !== id));
  };

  return (
    <div className="space-y-6" id="watchlist-page">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold font-heading text-white">Watchlist</h1>
          <p className="text-[var(--color-text-secondary)]">Monitor key assets and price alerts</p>
        </div>
        <div className="flex space-x-3">
          <Button variant="secondary" onClick={fetchWatchlist}>
            <RefreshCw size={14} className={`mr-2 ${loading ? 'animate-spin' : ''}`} /> Sync
          </Button>
          <Button onClick={() => setShowAddModal(true)}>
            <Plus size={16} className="mr-2" /> Add to Watchlist
          </Button>
        </div>
      </div>

      {items.length === 0 ? (
        <Card className="p-8 text-center">
          <h2 className="text-xl text-white mb-2">Your watchlist is empty</h2>
          <p className="text-[var(--color-text-secondary)]">
            Search for assets and add them to your watchlist to monitor them closely.
          </p>
        </Card>
      ) : (
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
                {items.map((item) => {
                  const isPositive = item.change >= 0;
                  return (
                    <tr key={item.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="px-6 py-4 font-bold text-white">{item.symbol}</td>
                      <td className="px-6 py-4 text-gray-300">{item.name}</td>
                      <td className="px-6 py-4 text-right text-white font-semibold">${item.price.toFixed(2)}</td>
                      <td className="px-6 py-4 text-right">
                        <div
                          className={`inline-flex items-center px-2.5 py-1 rounded-md text-sm font-medium ${
                            isPositive
                              ? 'bg-[var(--color-accent)]/10 text-[var(--color-accent)]'
                              : 'bg-[var(--color-danger)]/10 text-[var(--color-danger)]'
                          }`}
                        >
                          {isPositive ? <ArrowUpRight size={14} className="mr-1" /> : <ArrowDownRight size={14} className="mr-1" />}
                          {Math.abs(item.change)}%
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right text-[var(--color-primary-light)] font-medium">
                        {item.target_price ? `$${item.target_price.toFixed(2)}` : '—'}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <button
                          onClick={() => handleRemove(item.id)}
                          className="text-gray-500 hover:text-red-400 transition-colors cursor-pointer"
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
      )}

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
                <label className="block text-sm text-[var(--color-text-secondary)] mb-1">Symbol (e.g. NVDA)</label>
                <input
                  type="text"
                  required
                  value={symbolInput}
                  onChange={(e) => setSymbolInput(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-[var(--color-primary)]"
                  placeholder="NVDA"
                />
              </div>
              <div>
                <label className="block text-sm text-[var(--color-text-secondary)] mb-1">Company Name</label>
                <input
                  type="text"
                  value={nameInput}
                  onChange={(e) => setNameInput(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
                  placeholder="NVIDIA Corporation"
                />
              </div>
              <div>
                <label className="block text-sm text-[var(--color-text-secondary)] mb-1">Target Price Alert ($)</label>
                <input
                  type="number"
                  step="any"
                  value={targetInput}
                  onChange={(e) => setTargetInput(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
                  placeholder="140.00"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <Button variant="secondary" type="button" onClick={() => setShowAddModal(false)}>
                  Cancel
                </Button>
                <Button type="submit">Add Item</Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
