import React from 'react';
import { Database, Compass, FileText, Terminal, BarChart3 } from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, setCurrentTab }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Compass },
    { id: 'upload', label: 'Dataset Upload', icon: Database },
    { id: 'workspace', label: 'Analysis Workspace', icon: Terminal },
    { id: 'reports', label: 'Executive Reports', icon: FileText }
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-neutral-800 bg-black/90 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div 
          onClick={() => setCurrentTab('dashboard')}
          className="flex items-center space-x-3 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded-lg bg-white text-black flex items-center justify-center font-black transition-transform duration-200 group-hover:scale-105">
            <BarChart3 className="w-5 h-5 text-black" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight text-white">
                DataPilot
              </span>
              <span className="text-[10px] uppercase font-mono tracking-widest px-2 py-0.5 rounded bg-neutral-900 text-neutral-300 border border-neutral-700">
                Analytics
              </span>
            </div>
            <p className="text-xs text-neutral-400">Data Intelligence Platform</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-1 sm:space-x-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-white text-black font-semibold shadow-sm'
                    : 'text-neutral-400 hover:text-white hover:bg-neutral-900 border border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-black' : 'text-neutral-400'}`} />
                <span className="hidden md:inline">{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* System Status */}
        <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-neutral-900 border border-neutral-800 text-xs">
          <span className="h-2 w-2 rounded-full bg-white animate-pulse" />
          <span className="text-neutral-300 font-mono text-[11px]">System Ready</span>
        </div>
      </div>
    </header>
  );
};

