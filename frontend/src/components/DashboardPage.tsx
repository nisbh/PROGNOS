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
import {
  Shield,
  Target,
  Timer,
  Activity,
  HelpCircle,
  History,
  Clock,
  ChevronRight,
} from 'lucide-react';
import type { DashboardData } from '../types/dashboard';
import {
  getSeverityStyle,
  formatRiskScore,
  formatFeatureName,
  generatePlainEnglishExplanation,
  getSortedTrafficHistory,
  getSortedRiskHistory,
  formatTimestamp,
} from '../services/api';

interface DashboardPageProps {
  data: DashboardData;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ data }) => {
  const currentStatus = data.currentStatus;
  const forecast = data.forecast;
  const explanation = data.explanation;

  const currentClass = currentStatus?.risk_level || currentStatus?.class || 'NORMAL';
  const severity = getSeverityStyle(currentClass);
  const rawRiskScore = currentStatus?.risk_score ?? 0;
  const formattedRisk = formatRiskScore(rawRiskScore);
  const numericRisk = Math.min(100, Math.max(0, Number(rawRiskScore) || 0));

  const probability = Math.round((forecast?.probability ?? 0) * 100);
  const predictedClass = forecast?.class || currentClass;
  const predictedSeverity = getSeverityStyle(predictedClass);

  const etaWindow =
    forecast?.eta_window ||
    (currentClass === 'NORMAL' ? 'No active threat' : 'Calculating...');

  // Sort traffic points chronologically: oldest (LEFT) -> newest (RIGHT)
  const trafficPoints = getSortedTrafficHistory(data.traffic);
  const latestTraffic = trafficPoints[trafficPoints.length - 1];
  const currentConn = latestTraffic?.connections_per_sec ?? 0;
  const currentSyn = latestTraffic?.syn_rate ?? 0;

  // Model explanation features
  const features = explanation?.features || [];
  const maxShap = Math.max(...features.map((f) => Math.abs(f.shap_value)), 2.0);
  const humanExplanation = generatePlainEnglishExplanation(features, currentClass);

  // Sort history points chronologically: oldest (LEFT) -> newest (RIGHT)
  const historyItems = getSortedRiskHistory(data.history);

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto w-full">
      {/* ========================================================================= */}
      {/* 1. TOP ROW: 4 Compact Metric Cards                                       */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Current Risk */}
        <div className="soc-card p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-sky-400" />
              <span>Current Risk</span>
            </span>
            <span
              className={`px-2 py-0.5 rounded text-[11px] font-bold border ${severity.badgeBg}`}
            >
              {severity.label}
            </span>
          </div>

          <div className="my-3">
            <div className="flex items-baseline gap-1.5">
              <span className="text-3xl font-bold text-white tracking-tight">
                {formattedRisk}
              </span>
              <span className="text-xs text-slate-400 font-medium">/ 100</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              System risk assessment index
            </p>
          </div>

          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${numericRisk}%`,
                backgroundColor: severity.barColor,
              }}
            />
          </div>
        </div>

        {/* Card 2: Attack Forecast */}
        <div className="soc-card p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5 text-sky-400" />
              <span>Attack Forecast</span>
            </span>
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${predictedSeverity.badgeBg}`}
            >
              {predictedClass}
            </span>
          </div>

          <div className="my-3">
            <div className="flex items-baseline gap-1.5">
              <span className="text-3xl font-bold text-white tracking-tight">
                {probability}%
              </span>
              <span className="text-xs text-slate-400 font-medium">probability</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Impending attack likelihood
            </p>
          </div>

          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500 bg-sky-500"
              style={{ width: `${Math.min(100, Math.max(0, probability))}%` }}
            />
          </div>
        </div>

        {/* Card 3: Estimated Time to Attack */}
        <div className="soc-card p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
              <Timer className="w-3.5 h-3.5 text-sky-400" />
              <span>Time to Attack (ETA)</span>
            </span>
          </div>

          <div className="my-3">
            <div className="flex items-baseline">
              <span className={`text-2xl sm:text-3xl font-bold tracking-tight ${severity.textClass}`}>
                {etaWindow}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {currentClass === 'NORMAL'
                ? 'No active anomaly horizon'
                : 'Forecasted arrival window'}
            </p>
          </div>

          <div className="text-[11px] text-slate-400 pt-1.5 border-t border-slate-800 flex items-center justify-between">
            <span>Threat Status</span>
            <span className="font-semibold text-slate-200">{severity.label}</span>
          </div>
        </div>

        {/* Card 4: Network Activity */}
        <div className="soc-card p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-sky-400" />
              <span>Network Activity</span>
            </span>
            <span className="text-[10px] text-slate-500">Live Window</span>
          </div>

          <div className="my-2 grid grid-cols-2 gap-2">
            <div>
              <span className="text-xs text-slate-400 block">Conn / sec</span>
              <span className="text-xl font-bold text-white tracking-tight block">
                {currentConn.toLocaleString()}
              </span>
            </div>
            <div>
              <span className="text-xs text-slate-400 block">SYN Rate</span>
              <span className="text-xl font-bold text-rose-400 tracking-tight block">
                {currentSyn.toLocaleString()}
              </span>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 pt-1.5 border-t border-slate-800 flex items-center justify-between">
            <span>Ingress Streams</span>
            <span className="text-sky-400 font-medium">Active</span>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. SECOND ROW: Traffic Trend (65-70%) + Prediction Reasoning (30-35%)    */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Network Traffic Trend (lg:col-span-8 ≈ 67%) */}
        <div className="lg:col-span-8 soc-card p-6 flex flex-col justify-between">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <span>Network Traffic Trend</span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Sliding window telemetry (oldest on left → newest on right)
              </p>
            </div>

            {/* Restrained Legend */}
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-sky-400" />
                <span className="text-slate-300">Connections/sec</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-rose-400" />
                <span className="text-slate-300">SYN Rate</span>
              </div>
            </div>
          </div>

          {/* Area Chart with Restrained Fill */}
          <div className="w-full h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={trafficPoints}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="connSubtleFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="synSubtleFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.15} />
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
                  fill="url(#connSubtleFill)"
                />

                <Area
                  type="monotone"
                  dataKey="syn_rate"
                  name="SYN Rate"
                  stroke="#f43f5e"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#synSubtleFill)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Prediction Reasoning (lg:col-span-4 ≈ 33%) */}
        <div className="lg:col-span-4 soc-card p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <HelpCircle className="w-4 h-4 text-sky-400" />
              <h2 className="text-sm font-semibold text-slate-100">
                Prediction Reasoning
              </h2>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Features contributing most to the current forecast.
            </p>

            {/* Plain-English Summary Derived Strictly from Backend Features */}
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-xs leading-relaxed mb-4">
              <p className="font-normal text-slate-200">
                {humanExplanation}
              </p>
            </div>

            {/* Feature Weight Bars without snake_case */}
            <div className="flex flex-col gap-3">
              {features.length > 0 ? (
                features.map((feat, idx) => {
                  const widthPct = Math.min(
                    100,
                    Math.round((Math.abs(feat.shap_value) / maxShap) * 100)
                  );
                  const humanTitle = formatFeatureName(feat.name);

                  return (
                    <div
                      key={idx}
                      className="p-2.5 rounded-md bg-slate-900/90 border border-slate-800/80 flex flex-col gap-1.5"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-medium text-slate-200 truncate mr-2" title={humanTitle}>
                          {humanTitle}
                        </span>
                        <div className="flex items-center gap-2 text-right shrink-0">
                          <span className="text-[11px] text-sky-300 font-semibold">
                            {feat.actual_value}
                          </span>
                          <span className="text-[11px] font-mono text-slate-400">
                            +{feat.shap_value.toFixed(2)}
                          </span>
                        </div>
                      </div>

                      {/* Weight Progress Bar */}
                      <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-sky-500 transition-all duration-500"
                          style={{ width: `${widthPct}%` }}
                        />
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-xs text-slate-500 py-3 text-center">
                  No anomalous model triggers detected.
                </div>
              )}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 mt-4 text-[11px] text-slate-500 flex items-center justify-between">
            <span>Model Explainability</span>
            <span className="text-slate-400">SHAP Attributions</span>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3. BOTTOM ROW: Chronological Recent Risk History Timeline                 */}
      {/* ========================================================================= */}
      <div className="soc-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-sky-400" />
            <h2 className="text-sm font-semibold text-slate-100">
              Recent Risk History
            </h2>
          </div>
          <span className="text-xs text-slate-400">
            Chronological Progression (Oldest → Latest)
          </span>
        </div>

        {/* Timeline Progression Container */}
        <div className="w-full overflow-x-auto pb-1">
          {historyItems.length > 0 ? (
            <div className="flex items-center justify-between min-w-[580px] gap-2">
              {historyItems.map((item, idx) => {
                const itemSeverity = getSeverityStyle(item.class);
                const isLatest = idx === historyItems.length - 1;

                return (
                  <React.Fragment key={idx}>
                    {/* Progression Node */}
                    <div
                      className={`flex-1 p-3 rounded-lg border flex flex-col items-center text-center transition-all ${
                        isLatest
                          ? `${itemSeverity.bgClass} ${itemSeverity.borderClass} ring-1 ring-sky-500/20`
                          : 'bg-slate-900 border-slate-800'
                      }`}
                    >
                      <div className="flex items-center justify-between w-full mb-1 text-[10px]">
                        <span className="text-slate-500 font-mono">
                          #{idx + 1}
                        </span>
                        {isLatest && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-bold uppercase bg-sky-500/20 text-sky-300 border border-sky-500/30">
                            Current
                          </span>
                        )}
                      </div>

                      <span
                        className={`px-2.5 py-0.5 rounded text-xs font-bold border my-1 ${itemSeverity.badgeBg}`}
                      >
                        {itemSeverity.label}
                      </span>

                      <div className="flex items-center gap-1 text-[11px] text-slate-400 mt-1">
                        <Clock className="w-3 h-3 text-slate-500" />
                        <span>{formatTimestamp(item.ts)}</span>
                      </div>
                    </div>

                    {/* Arrow Connector between steps */}
                    {idx < historyItems.length - 1 && (
                      <div className="shrink-0 px-1 text-slate-600">
                        <ChevronRight className="w-4 h-4" />
                      </div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          ) : (
            <div className="text-center text-xs text-slate-500 py-4">
              No recent temporal windows recorded.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
