import { Card } from '../components/ui/Card';

export default function Watchlist() {
  return (
    <div className="space-y-6" id="watchlist-page">
      <h1 className="text-3xl font-bold font-heading text-white">Watchlist</h1>
      <Card className="p-8 text-center">
        <h2 className="text-xl text-white mb-2">Your watchlist is empty</h2>
        <p className="text-[var(--color-text-secondary)]">Search for assets and add them to your watchlist to monitor them closely.</p>
      </Card>
    </div>
  );
}
