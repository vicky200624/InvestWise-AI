import { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { authApi } from '../services/api';

export default function ConnectBroker() {
  const [brokerName, setBrokerName] = useState('Zerodha');
  const [accountId, setAccountId] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [linkedAccounts, setLinkedAccounts] = useState<any[]>([]);
  
  // Status message state to show errors or success in the UI
  const [statusMessage, setStatusMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);

  useEffect(() => {
    fetchLinkedBrokers();
  }, []);

  const fetchLinkedBrokers = async () => {
    setIsFetching(true);
    try {
      const data = await authApi.getLinkedBrokers();
      setLinkedAccounts(data);
    } catch (err: any) {
      console.error("Failed to load linked brokers", err);
      // SHOW ERROR in the UI instead of failing silently in the console
      setStatusMessage({ 
        type: 'error', 
        text: err.response?.data?.detail || 'Failed to load existing broker connections. Please refresh the page.' 
      });
    } finally {
      setIsFetching(false);
    }
  };

  const handleLinkAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setStatusMessage(null);

    try {
      await authApi.linkBroker({
        broker_name: brokerName,
        account_id: accountId,
        api_key_encrypted: apiKey,
        api_secret_encrypted: apiSecret
      });
      
      setStatusMessage({ type: 'success', text: 'Broker account linked successfully!' });
      setAccountId('');
      setApiKey('');
      setApiSecret('');
      
      // Refresh the list after linking
      fetchLinkedBrokers();
    } catch (err: any) {
      // Show specific duplicate error or fallback error
      if (err.response?.status === 409) {
        setStatusMessage({ type: 'error', text: 'This broker account is already linked to an account.' });
      } else {
        setStatusMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to link broker account.' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8 text-white">
      <div>
        <h1 className="text-3xl font-bold font-heading">Broker Account Integration</h1>
        <p className="text-gray-400 mt-1">Connect your portfolio accounts securely to InvestWise-AI</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <Card className="p-6 border border-white/10 bg-white/5 backdrop-blur-xl">
          <h2 className="text-xl font-semibold mb-4">Link New Account</h2>

          {/* Dynamic Error / Success Banner */}
          {statusMessage && (
            <div className={`mb-4 p-3 rounded-lg text-sm ${statusMessage.type === 'error' ? 'bg-red-500/20 text-red-300 border border-red-500/30' : 'bg-green-500/20 text-green-300 border border-green-500/30'}`}>
              {statusMessage.text}
            </div>
          )}

          <form onSubmit={handleLinkAccount} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Broker Platform</label>
              <select 
                value={brokerName} 
                onChange={(e) => setBrokerName(e.target.value)}
                className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white focus:outline-none focus:border-[var(--color-primary)]"
              >
                <option value="Zerodha">Zerodha (Kite)</option>
                <option value="Alpaca">Alpaca Markets</option>
                <option value="InteractiveBrokers">Interactive Brokers</option>
                <option value="Binance">Binance</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Account ID / Client ID</label>
              <input 
                type="text" 
                required 
                value={accountId} 
                onChange={(e) => setAccountId(e.target.value)}
                className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white focus:outline-none focus:border-[var(--color-primary)]"
                placeholder="e.g., AB1234"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">API Key</label>
              <input 
                type="text" 
                required 
                value={apiKey} 
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white focus:outline-none focus:border-[var(--color-primary)]"
                placeholder="Your broker API key"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">API Secret</label>
              <input 
                type="password" 
                value={apiSecret} 
                onChange={(e) => setApiSecret(e.target.value)}
                className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white focus:outline-none focus:border-[var(--color-primary)]"
                placeholder="••••••••••••"
              />
            </div>

            <Button type="submit" className="w-full py-3 mt-2" isLoading={isLoading}>
              Link Broker Account
            </Button>
          </form>
        </Card>

        <Card className="p-6 border border-white/10 bg-white/5 backdrop-blur-xl">
          <h2 className="text-xl font-semibold mb-4">Linked Broker Accounts</h2>
          
          {isFetching ? (
            <p className="text-sm text-gray-400">Loading your accounts...</p>
          ) : linkedAccounts.length === 0 ? (
            <p className="text-sm text-gray-400">No broker accounts connected yet.</p>
          ) : (
            <div className="space-y-3">
              {linkedAccounts.map((account) => (
                <div key={account.id} className="p-3 bg-black/20 border border-white/10 rounded-xl flex justify-between items-center">
                  <div>
                    <h3 className="font-semibold text-white">{account.broker_name}</h3>
                    <p className="text-xs text-gray-400">ID: {account.account_id}</p>
                  </div>
                  <span className="text-xs px-2.5 py-1 bg-emerald-500/20 text-emerald-300 rounded-full border border-emerald-500/30">
                    Connected
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}