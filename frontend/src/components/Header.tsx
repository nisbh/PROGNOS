import React from 'react';
import { Shield, LayoutDashboard, LineChart, ShieldAlert } from 'lucide-react';
import type { ActiveTab } from '../types/dashboard';

interface HeaderProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  backendOnline: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  backendOnline,
}) => {
  return (
    <header className="w-full bg-[#0d1322] border-b border-slate-800 sticky top-0 z-50 px-4 lg:px-8 py-3">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Left: Branding */}
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-slate-100 tracking-tight">
                PROGNOS
              </span>
              <span className="px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-slate-800 text-slate-400 border border-slate-700">
                SIH 2026
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Network Attack Forecasting System
            </p>
          </div>
        </div>

        {/* Center: Simple 3-Tab Navigation */}
        <nav className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-1">
          <button
            onClick={() => onTabChange('overview')}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition cursor-pointer ${
              activeTab === 'overview'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Overview</span>
          </button>

          <button
            onClick={() => onTabChange('analysis')}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition cursor-pointer ${
              activeTab === 'analysis'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <LineChart className="w-4 h-4" />
            <span>Analysis</span>
          </button>

          <button
            onClick={() => onTabChange('threat-context')}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition cursor-pointer ${
              activeTab === 'threat-context'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            <span>Threat Context</span>
          </button>
        </nav>

        {/* Right: Simple Connection Status */}
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span
            className={`w-2 h-2 rounded-full ${
              backendOnline ? 'bg-emerald-400' : 'bg-red-400'
            }`}
          />
          <span>{backendOnline ? 'Backend Connected' : 'Offline'}</span>
        </div>
      </div>
    </header>
  );
};