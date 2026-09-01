export type ThreatClass = 'NORMAL' | 'ELEVATED' | 'NEAR-TERM' | 'IMMINENT' | string;
export type ActiveTab = 'overview' | 'analysis' | 'threat-context';

export interface CurrentStatusResponse {
  risk_level: ThreatClass;
  risk_score: number;
  class: ThreatClass;
  ts: string;
}

export interface MitreTactic {
  id: string;
  name: string;
}

export interface MitreTechnique {
  id: string;
  name: string;
}

export interface MitreSubTechnique {
  id: string;
  name: string;
}

export interface MitreContext {
  tactic?: MitreTactic;
  technique?: MitreTechnique;
  sub_technique?: MitreSubTechnique;
  description?: string;
}

export interface ForecastResponse {
  class: ThreatClass;
  probability: number;
  eta_window: string;
  top_features: string[];
  mitre_context?: MitreContext;
}

export interface TrafficPoint {
  timestamp: string;
  connections_per_sec: number;
  syn_rate: number;
}

export interface TrafficResponse {
  history: TrafficPoint[];
}

export interface ExplanationFeature {
  name: string;
  shap_value: number;
  actual_value: string;
}

export interface ExplanationResponse {
  features: ExplanationFeature[];
}

export interface HistoryItem {
  ts: string;
  class: ThreatClass;
}

export interface HistoryResponse {
  history: HistoryItem[];
}

export interface DashboardData {
  currentStatus: CurrentStatusResponse | null;
  forecast: ForecastResponse | null;
  traffic: TrafficResponse | null;
  explanation: ExplanationResponse | null;
  history: HistoryResponse | null;
}

export interface SystemHealth {
  backendOnline: boolean;
  latencyMs: number;
  lastSuccessfulFetch: string | null;
  errorMessage: string | null;
  isPolling: boolean;
  pollIntervalSec: number;
  isDemoMode: boolean;
}