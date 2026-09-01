import React, { useState } from 'react';
import { History, Clock, Filter, AlertTriangle } from 'lucide-react';
import type { DashboardData } from '../types/dashboard';
import {
  getSeverityStyle,
  getHistoryNewestFirst,
  formatTimestamp,
} from '../services/api';

interface RiskHistoryPageProps {
  data: DashboardData;
}

type FilterWindow = 1 | 5 | 10; // in minutes

export const RiskHistoryPage: React.FC<RiskHistoryPageProps> = ({ data }) => {
  const [selectedFilter, setSelectedFilter] = useState<FilterWindow>(5);

  const filterOptions: { label: string; value: FilterWindow }[] = [
    { label: 'Last 1 Minute', value: 1 },
    { label: 'Last 5 Minutes', value: 5 },
    { label: 'Last 10 Minutes', value: 10 },
  ];

  // All history items sorted newest first
  const allHistory = getHistoryNewestFirst(data.history);

  // Filter based on actual record timestamp relative to current time
  const nowMs = Date.now();
  const filteredHistory = allHistory.filter((item) => {
    const itemMs = new Date(item.ts).getTime();
    if (isNaN(itemMs)) return true;
    return itemMs >= nowMs - selectedFilter * 60 * 1000;
  });

  const getRelativeTime = (isoString: string): string => {
    try {
      const diffSec = Math.max(0, Math.floor((Date.now() - new Date(isoString).getTime()) / 1000));
      if (diffSec < 15) return 'Just now';
      if (diffSec < 60) return `${diffSec}s ago`;
      const diffMin = Math.floor(diffSec / 60);
      const remSec = diffSec % 60;
      return `${diffMin}m ${remSec > 0 ? `${remSec}s` : ''} ago`;
    } catch {
      return '--';
    }
  };

  const getThreatDescription = (threatClass: string): string => {
    const normalized = threatClass.toUpperCase();
    switch (normalized) {
      case 'IMMINENT':
        return 'Critical threat state — immediate mitigation recommended';
      case 'NEAR-TERM':
        return 'High anomaly velocity — forecasted attack arrival in <2m';
      case 'ELEVATED':
        return 'Anomalous telemetry detected — heightened vigilance';
      case 'NORMAL':
      default:
        return 'Nominal traffic baseline — no anomalous indicators';
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto w-full">
      {/* 1. Header Banner */}
      <div className="soc-card p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400 shrink-0">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-100">
                Risk History
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Recent network risk classifications and attack forecasts (Newest First)
              </p>
            </div>
          </div>

          {/* Time Filter Controls */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 text-xs text-slate-400 mr-1 hidden md:flex">
              <Filter className="w-3.5 h-3.5 text-sky-400" />
              <span>Time Window:</span>
            </div>
            <div className="inline-flex rounded-lg bg-slate-900 border border-slate-800 p-1 gap-1">
              {filterOptions.map((opt) => {
                const isSelected = selectedFilter === opt.value;
                return (
                  <button
                    key={opt.value}
                    onClick={() => setSelectedFilter(opt.value)}
                    className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-150 cursor-pointer ${
                      isSelected
                        ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30 shadow-[0_0_12px_rgba(56,189,248,0.1)]'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                    }`}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* 2. History Table */}
      <div className="soc-card overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Temporal Classification Log
            </span>
            <span className="text-xs text-slate-500">
              ({filteredHistory.length} {filteredHistory.length === 1 ? 'event' : 'events'} in range)
            </span>
          </div>

          <span className="text-[11px] text-slate-500 font-mono">
            Auto-refreshing every 3.0s
          </span>
        </div>

        {filteredHistory.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-800/80 bg-slate-900/60 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-6">Timestamp</th>
                  <th className="py-3 px-6">Relative Age</th>
                  <th className="py-3 px-6">Risk Classification</th>
                  <th className="py-3 px-6">Telemetry Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {filteredHistory.map((item, idx) => {
                  const severity = getSeverityStyle(item.class);
                  const isLatest = idx === 0;

                  return (
                    <tr
                      key={`${item.ts}-${idx}`}
                      className="hover:bg-slate-800/30 transition-colors"
                    >
                      {/* Column 1: Time */}
                      <td className="py-3.5 px-6 font-mono text-xs text-slate-300">
                        <div className="flex items-center gap-2">
                          <Clock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                          <span>{formatTimestamp(item.ts)}</span>
                          {isLatest && (
                            <span className="px-1.5 py-0.2 rounded text-[9px] font-bold uppercase bg-sky-500/20 text-sky-300 border border-sky-500/30">
                              Latest
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Column 2: Relative Time */}
                      <td className="py-3.5 px-6 text-xs text-slate-400">
                        {getRelativeTime(item.ts)}
                      </td>

                      {/* Column 3: Risk Classification */}
                      <td className="py-3.5 px-6">
                        <span
                          className={`inline-block px-2.5 py-0.5 rounded text-xs font-bold border ${severity.badgeBg}`}
                        >
                          {severity.label}
                        </span>
                      </td>

                      {/* Column 4: Description */}
                      <td className="py-3.5 px-6 text-xs text-slate-400 max-w-md">
                        {getThreatDescription(item.class)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          /* Empty State */
          <div className="p-12 flex flex-col items-center justify-center text-center">
            <div className="w-10 h-10 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500 mb-3">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <h4 className="text-sm font-semibold text-slate-200">
              No risk events recorded in this time window.
            </h4>
            <p className="text-xs text-slate-500 mt-1 max-w-sm">
              Try selecting a wider time range (e.g. Last 5 Minutes or Last 10 Minutes) to inspect past classification history.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
