import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { Shield, Target, Timer, History, Clock } from 'lucide-react';
import type { DashboardData } from '../types/dashboard';
import { getSeverityStyle, formatTimestamp } from '../services/api';

interface OverviewTabProps {
  data: DashboardData;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({ data }) => {
  const currentStatus = data.currentStatus;
  const forecast = data.forecast;
  const traffic = data.traffic;
  const history = data.history;

  const currentClass = currentStatus?.risk_level || currentStatus?.class || 'NORMAL';
  const severity = getSeverityStyle(currentClass);
  const riskScore = currentStatus?.risk_score ?? 10;
  const probability = Math.round((forecast?.probability ?? 0.1) * 100);
  const etaWindow = forecast?.eta_window || (currentClass === 'NORMAL' ? 'N/A' : 'Calculating...');

  // Format traffic points for Recharts
  const trafficPoints = (traffic?.history || []).map((pt) => ({
    ...pt,
    time: formatTimestamp(pt.timestamp),
  }));

  const historyItems = history?.history || [];

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto w-full">
      {/* 1. Top Summary Cards (Risk, Forecast, ETA) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Card 1: Current Risk Level & Score */}
        <div className="soc-card p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-400 text-sm font-medium">
              <Shield className="w-4 h-4 text-sky-400" />
              <span>Current Risk</span>
            </div>
            <span
              className={`px-2.5 py-0.5 rounded text-xs font-bold border ${severity.badgeBg}`}
            >
              {severity.label}
            </span>
          </div>

          <div className="my-4">
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold text-white tracking-tight">
                {riskScore}
              </span>
              <span className="text-sm text-slate-400 font-medium">/ 100</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">Overall system risk index</p>
          </div>

          {/* Simple Severity Progress Bar */}
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${Math.min(100, Math.max(0, riskScore))}%`,
                backgroundColor: severity.barColor,
              }}
            />
          </div>
        </div>

        {/* Card 2: Forecast Probability */}
        <div className="soc-card p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-400 text-sm font-medium">
              <Target className="w-4 h-4 text-sky-400" />
              <span>Attack Forecast</span>
            </div>
            <span className="text-xs font-semibold text-slate-300">
              Class: {forecast?.class || currentClass}
            </span>
          </div>

          <div className="my-4">
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-bold text-white tracking-tight">
                {probability}%
              </span>
              <span className="text-sm text-slate-400 font-medium">probability</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">Likelihood of impending attack</p>
          </div>

          {/* Probability Bar */}
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500 bg-sky-500"
              style={{ width: `${Math.min(100, Math.max(0, probability))}%` }}
            />
          </div>
        </div>

        {/* Card 3: Attack ETA Window */}
        <div className="soc-card p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-400 text-sm font-medium">
              <Timer className="w-4 h-4 text-sky-400" />
              <span>Estimated Time to Attack</span>
            </div>
          </div>

          <div className="my-4">
            <div className="flex items-baseline">
              <span className={`text-4xl font-bold tracking-tight ${severity.textClass}`}>
                {etaWindow}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {currentClass === 'NORMAL'
                ? 'No immediate attack predicted'
                : 'Forecasted arrival window'}
            </p>
          </div>

          <div className="text-xs text-slate-400 pt-2 border-t border-slate-800">
            Status: <span className="font-semibold text-slate-200">{severity.label}</span>
          </div>
        </div>
      </div>

      {/* 2. Network Traffic Trend Chart */}
      <div className="soc-card p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              Network Traffic Trend
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live comparison of total connections/sec and SYN packet rate
            </p>
          </div>

          {/* Clean Legend */}
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-sky-400" />
              <span className="text-slate-300">Connections / sec</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-rose-400" />
              <span className="text-slate-300">SYN Rate</span>
            </div>
          </div>
        </div>

        {/* Recharts Area Chart */}
        <div className="w-full h-72">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={trafficPoints}
              margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
            >
              <defs>
                <linearGradient id="connFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="synFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
                </linearGradient>
              </defs>

              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#1f2937"
                vertical={false}
              />

              <XAxis
                dataKey="time"
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: '#334155' }}
              />

              <YAxis
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: '#334155' }}
                tickFormatter={(v) => (v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v)}
              />

              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  borderColor: '#334155',
                  borderRadius: '0.5rem',
                  fontSize: '12px',
                  color: '#f8fafc',
                }}
              />

              <Area
                type="monotone"
                dataKey="connections_per_sec"
                name="Connections/sec"
                stroke="#38bdf8"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#connFill)"
              />

              <Area
                type="monotone"
                dataKey="syn_rate"
                name="SYN Rate"
                stroke="#f43f5e"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#synFill)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 3. Recent Risk History */}
      <div className="soc-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-sky-400" />
            <h2 className="text-base font-semibold text-slate-100">
              Recent Risk History
            </h2>
          </div>
          <span className="text-xs text-slate-400">Last 5 Windows</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
          {historyItems.length > 0 ? (
            historyItems.map((item, idx) => {
              const itemSeverity = getSeverityStyle(item.class);
              return (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex flex-col items-center justify-center gap-1.5 text-center"
                >
                  <span
                    className={`px-2.5 py-0.5 rounded text-xs font-bold border ${itemSeverity.badgeBg}`}
                  >
                    {itemSeverity.label}
                  </span>
                  <div className="flex items-center gap-1 text-[11px] text-slate-400 mt-1">
                    <Clock className="w-3 h-3 text-slate-500" />
                    <span>{formatTimestamp(item.ts)}</span>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="col-span-5 text-center text-xs text-slate-500 py-3">
              No recent history recorded.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};