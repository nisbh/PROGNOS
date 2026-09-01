import React from 'react';
import type { ActiveTab } from '../types/dashboard';

interface TopHeaderProps {
  activeTab: ActiveTab;
  backendOnline: boolean;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  activeTab,
  backendOnline,
}) => {
  return (
    <header className="w-full bg-[#0d1322]/80 backdrop-blur-sm border-b border-slate-800/80 sticky top-0 z-40 px-6 py-3.5 flex items-center justify-between">
      {/* Breadcrumb / Section Title */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-slate-400 font-medium">SOC Console</span>
        <span className="text-slate-600">/</span>
        <span className="text-slate-100 font-semibold">
          {activeTab === 'dashboard' ? 'Security Dashboard' : 'Threat Context (MITRE ATT&CK®)'}
        </span>
      </div>

      {/* Backend Status Indicator */}
      <div className="flex items-center gap-2 text-xs">
        <span
          className={`w-2 h-2 rounded-full ${
            backendOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
          }`}
        />
        <span className="text-slate-300 font-medium">
          {backendOnline ? 'Backend Connected' : 'Disconnected'}
        </span>
      </div>
    </header>
  );
};
