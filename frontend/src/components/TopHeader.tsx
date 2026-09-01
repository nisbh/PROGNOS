import React, { useState, useEffect } from 'react';
import type { ActiveTab } from '../types/dashboard';

interface TopHeaderProps {
  activeTab: ActiveTab;
  backendOnline: boolean;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  activeTab,
  backendOnline,
}) => {
  const [time, setTime] = useState<{ local: string; utc: string }>({
    local: '',
    utc: '',
  });

  useEffect(() => {
    const updateClocks = () => {
      const now = new Date();
      setTime({
        local: now.toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: true,
        }),
        utc: now.toLocaleTimeString('en-US', {
          timeZone: 'UTC',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: true,
        }),
      });
    };

    updateClocks();
    const interval = setInterval(updateClocks, 1000);
    return () => clearInterval(interval);
  }, []);

  const getPageTitle = () => {
    switch (activeTab) {
      case 'dashboard':
        return 'Security Dashboard';
      case 'threat-context':
        return 'Threat Context (MITRE ATT&CK®)';
      case 'risk-history':
        return 'Risk History Log';
      default:
        return 'Security Dashboard';
    }
  };

  return (
    <header className="w-full bg-[#0d1322]/80 backdrop-blur-sm border-b border-slate-800/80 sticky top-0 z-40 px-6 py-3 flex items-center justify-between relative select-none">
      {/* 1. Left: Breadcrumb / Page Title */}
      <div className="flex items-center gap-2 text-sm z-10">
        <span className="text-slate-400 font-medium">SOC Console</span>
        <span className="text-slate-600">/</span>
        <span className="text-slate-100 font-semibold">
          {getPageTitle()}
        </span>
      </div>

      {/* 2. Center: Local Time + UTC Clocks */}
      <div className="hidden sm:flex items-center gap-4 absolute left-1/2 -translate-x-1/2 text-xs py-1 px-3 rounded-md bg-slate-900/60 border border-slate-800/60 shadow-xs">
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            LOCAL
          </span>
          <span className="font-mono tabular-nums text-slate-200 font-medium">
            {time.local || '--:--:-- --'}
          </span>
        </div>

        <span className="text-slate-700">|</span>

        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-sky-400">
            UTC
          </span>
          <span className="font-mono tabular-nums text-slate-200 font-medium">
            {time.utc || '--:--:-- --'}
          </span>
        </div>
      </div>

      {/* 3. Right: Backend Status Indicator */}
      <div className="flex items-center gap-2 text-xs z-10">
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
