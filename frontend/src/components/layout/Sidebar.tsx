import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, PieChart, Search, Eye, MessageSquare, Settings, LogOut } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';

const navItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/portfolio', icon: PieChart, label: 'Portfolio' },
  { path: '/research', icon: Search, label: 'Research' },
  { path: '/watchlist', icon: Eye, label: 'Watchlist' },
  { path: '/chat', icon: MessageSquare, label: 'AI Chat' },
];

export default function Sidebar() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <motion.aside
      initial={{ x: -250 }}
      animate={{ x: 0 }}
      className="w-64 border-r border-[var(--color-border)] bg-[var(--color-surface)] flex flex-col z-20"
      id="main-sidebar"
    >
      <div className="h-16 flex items-center px-6 border-b border-[var(--color-border)]">
        <div className="w-8 h-8 rounded bg-gradient-to-tr from-[var(--color-primary)] to-[var(--color-accent)] mr-3 shadow-lg shadow-primary/20"></div>
        <h1 className="text-xl font-bold font-heading bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70">InvestWise-AI</h1>
      </div>

      <nav className="flex-1 px-4 py-6 space-y-2">
        {navItems.map(({ path, icon: Icon, label }) => (
          <NavLink
            key={path}
            to={path}
            id={`nav-${label.toLowerCase()}`}
            className={({ isActive }) =>
              `flex items-center px-4 py-3 rounded-xl transition-all duration-200 group ${
                isActive
                  ? 'bg-[var(--color-primary)]/10 text-[var(--color-primary-light)] font-medium'
                  : 'text-[var(--color-text-secondary)] hover:bg-white/5 hover:text-white'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={20} className={`mr-3 ${isActive ? 'text-[var(--color-primary-light)]' : 'group-hover:text-white transition-colors'}`} />
                {label}
                {isActive && (
                  <motion.div layoutId="nav-indicator" className="absolute left-0 w-1 h-8 bg-[var(--color-primary)] rounded-r-full" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-[var(--color-border)] space-y-2">
        <button id="nav-settings" className="flex items-center px-4 py-2 w-full text-sm text-[var(--color-text-secondary)] hover:text-white transition-colors">
          <Settings size={16} className="mr-3" /> Settings
        </button>
        <button id="nav-logout" onClick={handleLogout} className="flex items-center px-4 py-2 w-full text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors">
          <LogOut size={16} className="mr-3" /> Logout
        </button>
      </div>
    </motion.aside>
  );
}
