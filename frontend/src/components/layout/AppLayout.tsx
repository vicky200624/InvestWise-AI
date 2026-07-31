import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function AppLayout() {
  return (
    <div id="app-layout" className="flex h-screen bg-[var(--color-bg-base)] overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden relative">
        <TopBar />
        <main id="main-content" className="flex-1 overflow-y-auto p-6 relative z-10">
          {/* Subtle background glow */}
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-[var(--color-primary)]/10 rounded-full blur-3xl -z-10 pointer-events-none" />
          <Outlet />
        </main>
      </div>
    </div>
  );
}
