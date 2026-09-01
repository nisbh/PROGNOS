import React from 'react';
import { HelpCircle, Network, Flame, History, Clock } from 'lucide-react';
import type { DashboardData } from '../types/dashboard';
import {
  formatFeatureName,
  generatePlainEnglishExplanation,
  getSeverityStyle,
  formatTimestamp,
} from '../services/api';

interface AnalysisTabProps {
  data: DashboardData;
}

export const AnalysisTab: React.FC<AnalysisTabProps> = ({ data }) => {
  const currentStatus = data.currentStatus;
  const forecast = data.forecast;
  const explanation = data.explanation;
  const traffic = data.traffic;
  const history = data.history;

  const currentClass = currentStatus?.risk_level || forecast?.class || 'NORMAL';
  const features = explanation?.features || [];

  // Find latest traffic point
  const trafficPoints = traffic?.history || [];
  const latestTraffic = trafficPoints[trafficPoints.length - 1];
  const currentConn = latestTraffic?.connections_per_sec ?? 0;
  const currentSyn = latestTraffic?.syn_rate ?? 0;

  // Max SHAP for proportional bar width
  const maxShap = Math.max(...features.map((f) => Math.abs(f.shap_value)), 2.5);

  const humanExplanation = generatePlainEnglishExplanation(features, currentClass);

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto w-full">
      {/* 1. "Why this prediction?" Section */}
      <div className="soc-card p-6">
        <div className="flex items-center gap-2 mb-2">
          <HelpCircle className="w-5 h-5 text-sky-400" />
          <h2 className="text-lg font-semibold text-slate-100">
            Why this prediction?
          </h2>
        </div>
        <p className="text-xs text-slate-400 mb-5">
          Breakdown of telemetry features that contributed most heavily to the current risk forecast.
        </p>

        {/* Human Explanation Callout */}
        <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-sm leading-relaxed mb-6">
          <p className="font-medium text-slate-200">
            {humanExplanation}
          </p>
        </div>

        {/* Feature Contribution Bars */}
        <div className="flex flex-col gap-4">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Top Contributing Features
          </h3>

          {features.length > 0 ? (
            features.map((feat, idx) => {
              const widthPct = Math.min(100, Math.round((Math.abs(feat.shap_value) / maxShap) * 100));
              return (
                <div
                  key={idx}
                  className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 flex flex-col gap-2"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium text-slate-200 block">
                        {formatFeatureName(feat.name)}
                      </span>
                      <span className="text-xs text-slate-400 block font-mono">
                        {feat.name}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-right">
                      <div>
                        <span className="text-xs text-slate-400 block">Value</span>
                        <span className="text-xs font-semibold text-sky-300">
                          {feat.actual_value}
                        </span>
                      </div>
                      <div>
                        <span className="text-xs text-slate-400 block">Weight</span>
                        <span className="text-xs font-bold text-slate-200 font-mono">
                          +{feat.shap_value.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Horizontal Contribution Bar */}
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-sky-500 transition-all duration-500"
                      style={{ width: `${widthPct}%` }}
                    />
                  </div>
                </div>
              );
            })
          ) : (
            <p className="text-xs text-slate-500 py-2">
              No specific anomaly features reported in current window.
            </p>
          )}
        </div>
      </div>

      {/* 2. Current Traffic Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div className="soc-card p-6">
          <div className="flex items-center gap-2 text-slate-400 text-sm font-medium mb-3">
            <Network className="w-4 h-4 text-sky-400" />
            <span>Connections / sec</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white tracking-tight">
              {currentConn.toLocaleString()}
            </span>
            <span className="text-xs text-slate-400">connections per second</span>
          </div>
          <p className="text-xs text-slate-400 mt-2">
            Total active ingress sessions in latest temporal window.
          </p>
        </div>

        <div className="soc-card p-6">
          <div className="flex items-center gap-2 text-slate-400 text-sm font-medium mb-3">
            <Flame className="w-4 h-4 text-sky-400" />
            <span>SYN Packet Rate</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white tracking-tight">
              {currentSyn.toLocaleString()}
            </span>
            <span className="text-xs text-slate-400">packets per second</span>
          </div>
          <p className="text-xs text-slate-400 mt-2">
            Frequency of TCP handshake initiation packets.
          </p>
        </div>
      </div>

      {/* 3. Classification History Table */}
      <div className="soc-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <History className="w-4 h-4 text-sky-400" />
          <h2 className="text-base font-semibold text-slate-100">
            Recent Risk History
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase">
                <th className="pb-3 pr-4">Window Time</th>
                <th className="pb-3 px-4">Risk Classification</th>
                <th className="pb-3 pl-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {(history?.history || []).map((item, idx) => {
                const itemSev = getSeverityStyle(item.class);
                return (
                  <tr key={idx} className="hover:bg-slate-900/40">
                    <td className="py-3 pr-4 text-xs font-mono text-slate-300 flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>{formatTimestamp(item.ts)}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded text-xs font-semibold border ${itemSev.badgeBg}`}
                      >
                        {itemSev.label}
                      </span>
                    </td>
                    <td className="py-3 pl-4 text-right text-xs text-slate-400">
                      {idx === 0 ? 'Latest' : `${idx * 10}s prior`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};