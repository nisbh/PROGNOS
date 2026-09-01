import React from 'react';
import { ShieldAlert, Crosshair, BookOpen, CheckCircle2, ShieldCheck } from 'lucide-react';
import type { DashboardData } from '../types/dashboard';
import { getSeverityStyle } from '../services/api';

interface ThreatContextPageProps {
  data: DashboardData;
}

export const ThreatContextPage: React.FC<ThreatContextPageProps> = ({ data }) => {
  const forecast = data.forecast;
  const currentStatus = data.currentStatus;
  const currentClass = currentStatus?.risk_level || forecast?.class || 'NORMAL';
  const severity = getSeverityStyle(currentClass);
  const mitre = forecast?.mitre_context;

  const isThreatActive = currentClass !== 'NORMAL' && !!mitre;

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto w-full">
      {/* 1. Header Banner / Threat Context Overview */}
      <div className="soc-card p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400 shrink-0">
              <Crosshair className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-100">
                Threat Context (MITRE ATT&CK®)
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Adversary technique classification mapped directly to the MITRE knowledge base
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">Current Classification:</span>
            <span
              className={`px-3 py-1 rounded text-xs font-bold border ${severity.badgeBg}`}
            >
              {isThreatActive ? severity.label : 'BASELINE'}
            </span>
          </div>
        </div>
      </div>

      {isThreatActive ? (
        <>
          {/* 2. MITRE ATT&CK Matrix Hierarchy (Tactic, Technique, Sub-technique) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Tactic */}
            <div className="soc-card p-5 flex flex-col justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">
                  Tactic ({mitre.tactic?.id || 'TA0040'})
                </span>
                <span className="text-base font-bold text-slate-100 block mt-1">
                  {mitre.tactic?.name || 'Impact'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-3 pt-3 border-t border-slate-800/80 leading-relaxed">
                The adversary is attempting to degrade or interrupt network service availability.
              </p>
            </div>

            {/* Technique */}
            <div className="soc-card p-5 flex flex-col justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">
                  Technique ({mitre.technique?.id || 'T1499'})
                </span>
                <span className="text-base font-bold text-slate-100 block mt-1">
                  {mitre.technique?.name || 'Endpoint Denial of Service'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-3 pt-3 border-t border-slate-800/80 leading-relaxed">
                Adversary leverages protocol exploits to consume target connection capacity.
              </p>
            </div>

            {/* Sub-Technique */}
            <div className="soc-card p-5 flex flex-col justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">
                  Sub-Technique ({mitre.sub_technique?.id || 'T1499.004'})
                </span>
                <span className="text-base font-bold text-slate-100 block mt-1">
                  {mitre.sub_technique?.name || 'Application or System Exploitation'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-3 pt-3 border-t border-slate-800/80 leading-relaxed">
                Exhausts socket limits by holding pending half-open TCP states.
              </p>
            </div>
          </div>

          {/* 3. Adversary Behavior Description */}
          <div className="soc-card p-6">
            <div className="flex items-center gap-2 mb-2.5">
              <BookOpen className="w-4 h-4 text-sky-400" />
              <h3 className="text-sm font-semibold text-slate-100">
                Pattern Description
              </h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {mitre.description ||
                "Attempts to exhaust server resources by sending high rates of TCP SYN packets and maintaining half-open connections."}
            </p>
          </div>

          {/* 4. Suggested Operator Actions (Max 3 items, clearly labeled as suggestions) */}
          <div className="soc-card p-6">
            <div className="flex items-center gap-2 mb-1.5">
              <ShieldAlert className="w-4 h-4 text-sky-400" />
              <h3 className="text-sm font-semibold text-slate-100">
                Suggested Actions (Operator Guidance)
              </h3>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Standard mitigation procedures recommended for this attack profile (for operator review):
            </p>

            <ul className="flex flex-col gap-3">
              <li className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 flex items-start gap-3">
                <CheckCircle2 className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-medium text-slate-200 block">
                    1. Enable SYN Cookies on Edge Firewall
                  </span>
                  <span className="text-[11px] text-slate-400 block mt-0.5">
                    Mitigate backlog queue saturation by offloading half-open handshake state.
                  </span>
                </div>
              </li>

              <li className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 flex items-start gap-3">
                <CheckCircle2 className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-medium text-slate-200 block">
                    2. Apply Source IP Rate Limiting
                  </span>
                  <span className="text-[11px] text-slate-400 block mt-0.5">
                    Throttle aggressive new session handshakes per remote source address.
                  </span>
                </div>
              </li>

              <li className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 flex items-start gap-3">
                <CheckCircle2 className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-medium text-slate-200 block">
                    3. Inspect Target Application Ports
                  </span>
                  <span className="text-[11px] text-slate-400 block mt-0.5">
                    Verify connection timeout and keep-alive limits on targeted HTTP/TCP service ports.
                  </span>
                </div>
              </li>
            </ul>
          </div>
        </>
      ) : (
        /* Baseline State */
        <div className="soc-card p-12 flex flex-col items-center justify-center text-center">
          <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-4">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-100">
            No Active Adversary TTPs Mapped
          </h3>
          <p className="text-xs text-slate-400 max-w-md mt-1.5 leading-relaxed">
            Network traffic is operating within normal baseline boundaries. When anomalies trigger an elevated forecast, relevant MITRE ATT&CK tactics, techniques, and suggested actions will appear here.
          </p>
        </div>
      )}
    </div>
  );
};
