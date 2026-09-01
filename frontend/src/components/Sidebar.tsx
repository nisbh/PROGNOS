import React, { useRef, useState } from 'react';
import { LayoutDashboard, ShieldAlert, Shield, Radio, Activity, UploadCloud, Loader2 } from 'lucide-react';
import type { ActiveTab } from '../types/dashboard';
import { uploadReplay } from '../services/api';

interface SidebarProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  backendOnline: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  backendOnline,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setIsUploading(true);
      await uploadReplay(file);
      // Reset input so the same file can be uploaded again if needed
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload replay CSV. Ensure the backend is running.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <aside className="w-64 bg-[#0d1322] border-r border-slate-800/80 flex flex-col shrink-0 min-h-screen select-none">
      {/* 1. Brand / Header */}
      <div className="p-5 border-b border-slate-800/80 flex items-center gap-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-400 shadow-sm shrink-0">
          <Shield className="w-5 h-5" />
        </div>
        <div className="flex flex-col min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-base font-bold text-white tracking-tight">
              PROGNOS
            </span>
            <span className="px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider rounded bg-slate-800 text-sky-400 border border-slate-700">
              SIH 2026
            </span>
          </div>
          <span className="text-[11px] text-slate-400 truncate">
            Network Attack Forecasting
          </span>
        </div>
      </div>

      {/* 2. Upload Custom Replay */}
      <div className="px-3 pt-5 pb-2 flex flex-col gap-2 border-b border-slate-800/80">
        <div className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Simulation Data
        </div>
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
          accept=".csv" 
          className="hidden" 
        />
        <button
          onClick={handleUploadClick}
          disabled={isUploading || !backendOnline}
          className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-200 border ${
            isUploading || !backendOnline
              ? 'bg-slate-900 border-slate-800 text-slate-500 cursor-not-allowed'
              : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30 hover:bg-indigo-500/20 hover:border-indigo-500/50 shadow-[0_0_12px_rgba(99,102,241,0.1)] cursor-pointer'
          }`}
        >
          <div className="flex items-center gap-2.5">
            {isUploading ? (
              <Loader2 className="w-4 h-4 shrink-0 animate-spin text-indigo-400" />
            ) : (
              <UploadCloud className="w-4 h-4 shrink-0" />
            )}
            <span>{isUploading ? 'Uploading...' : 'Upload Custom CSV'}</span>
          </div>
        </button>
      </div>

      {/* 3. Navigation Items */}
      <div className="flex-1 py-4 px-3 flex flex-col gap-1.5">
        <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Navigation
        </div>

        {/* Dashboard Nav Link */}
        <button
          onClick={() => onTabChange('dashboard')}
          className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all duration-200 cursor-pointer ${
            activeTab === 'dashboard'
              ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30 shadow-[0_0_12px_rgba(56,189,248,0.1)]'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
          }`}
        >
          <LayoutDashboard className="w-4 h-4 shrink-0" />
          <span>Dashboard</span>
        </button>

        {/* Threat Context Nav Link */}
        <button
          onClick={() => onTabChange('threat-context')}
          className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all duration-200 cursor-pointer ${
            activeTab === 'threat-context'
              ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30 shadow-[0_0_12px_rgba(56,189,248,0.1)]'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
          }`}
        >
          <ShieldAlert className="w-4 h-4 shrink-0" />
          <span>Threat Context</span>
        </button>

        {/* System Monitoring Section */}
        <div className="mt-8 px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          System Feed
        </div>

        <div className="mx-1 p-3 rounded-lg bg-slate-900/80 border border-slate-800/80 flex flex-col gap-2.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 text-sky-400" />
              <span>FastAPI Backend</span>
            </span>
            <span
              className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                backendOnline
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  backendOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
                }`}
              />
              {backendOnline ? 'Online' : 'Offline'}
            </span>
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/80">
            <span className="flex items-center gap-1">
              <Activity className="w-3 h-3 text-slate-500" />
              <span>Telemetry Rate</span>
            </span>
            <span className="text-slate-300 font-mono">3.0s polling</span>
          </div>
        </div>
      </div>

      {/* 3. Footer info */}
      <div className="p-4 border-t border-slate-800/80 text-[11px] text-slate-400 flex flex-col gap-1">
        <div className="font-semibold text-slate-400">PROGNOS v2.0</div>
        <div className="text-[10px]">AI-driven SOC Early Warning</div>
      </div>
    </aside>
  );
};
