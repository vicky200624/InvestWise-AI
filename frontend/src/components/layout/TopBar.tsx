import { Bell, Search } from 'lucide-react';

export default function TopBar() {
  return (
    <header id="top-bar" className="h-16 border-b border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-md flex items-center justify-between px-6 z-20">
      <div className="flex items-center bg-white/5 border border-white/10 rounded-full px-4 py-2 w-96 focus-within:border-[var(--color-primary)]/50 transition-colors">
        <Search size={16} className="text-[var(--color-text-secondary)] mr-2" />
        <input 
          id="global-search"
          type="text" 
          placeholder="Search stocks, mutual funds, news..." 
          className="bg-transparent border-none outline-none text-sm w-full text-white placeholder-[var(--color-text-secondary)]"
        />
      </div>
      
      <div className="flex items-center space-x-4">
        <button id="notifications-btn" className="relative p-2 rounded-full hover:bg-white/10 transition-colors text-[var(--color-text-secondary)] hover:text-white">
          <Bell size={20} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[var(--color-primary)] rounded-full border border-[var(--color-surface)]"></span>
        </button>
        <div id="user-avatar" className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 border-2 border-[var(--color-surface-elevated)] cursor-pointer"></div>
      </div>
    </header>
  );
}
