import type {
  CurrentStatusResponse,
  ForecastResponse,
  TrafficResponse,
  ExplanationResponse,
  HistoryResponse,
  DashboardData,
  ThreatClass,
  ExplanationFeature,
} from '../types/dashboard';

export const API_BASE_URL = 'http://127.0.0.1:8000';

const FETCH_TIMEOUT_MS = 4000;

async function fetchWithTimeout(url: string, options: RequestInit = {}): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function fetchCurrentStatus(baseUrl: string = API_BASE_URL): Promise<CurrentStatusResponse> {
  const res = await fetchWithTimeout(`${baseUrl}/current-status`);
  if (!res.ok) throw new Error(`Failed to fetch current status (HTTP ${res.status})`);
  return res.json();
}

export async function fetchForecast(baseUrl: string = API_BASE_URL): Promise<ForecastResponse> {
  const res = await fetchWithTimeout(`${baseUrl}/forecast`);
  if (!res.ok) throw new Error(`Failed to fetch forecast (HTTP ${res.status})`);
  return res.json();
}

export async function fetchTraffic(baseUrl: string = API_BASE_URL): Promise<TrafficResponse> {
  const res = await fetchWithTimeout(`${baseUrl}/traffic`);
  if (!res.ok) throw new Error(`Failed to fetch traffic (HTTP ${res.status})`);
  return res.json();
}

export async function fetchExplanation(baseUrl: string = API_BASE_URL): Promise<ExplanationResponse> {
  const res = await fetchWithTimeout(`${baseUrl}/explanation`);
  if (!res.ok) throw new Error(`Failed to fetch explanation (HTTP ${res.status})`);
  return res.json();
}

export async function fetchHistory(limit: number = 5, baseUrl: string = API_BASE_URL): Promise<HistoryResponse> {
  const res = await fetchWithTimeout(`${baseUrl}/history?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch history (HTTP ${res.status})`);
  return res.json();
}

export interface FetchResult {
  data: DashboardData;
  error: string | null;
}

export async function fetchAllDashboardData(baseUrl: string = API_BASE_URL): Promise<FetchResult> {
  try {
    const [currentStatus, forecast, traffic, explanation, history] = await Promise.all([
      fetchCurrentStatus(baseUrl),
      fetchForecast(baseUrl),
      fetchTraffic(baseUrl),
      fetchExplanation(baseUrl),
      fetchHistory(5, baseUrl),
    ]);

    return {
      data: {
        currentStatus,
        forecast,
        traffic,
        explanation,
        history,
      },
      error: null,
    };
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : 'Cannot connect to FastAPI backend';
    return {
      data: {
        currentStatus: null,
        forecast: null,
        traffic: null,
        explanation: null,
        history: null,
      },
      error: errorMessage,
    };
  }
}

// Format exact backend feature names cleanly without inventing new concepts
export function formatFeatureName(rawName: string): string {
  switch (rawName) {
    case 'SYN_rate_slope':
      return 'SYN Rate Slope';
    case 'unique_source_ips_pct_change':
      return 'Unique Source IPs (% change)';
    case 'connection_count':
      return 'Connection Count';
    case 'connection_count_rolling_mean':
      return 'Connection Count (Rolling Mean)';
    default:
      return rawName.replace(/_/g, ' ');
  }
}

// Generate simple plain-English explanation strictly based on actual backend features
export function generatePlainEnglishExplanation(
  features: ExplanationFeature[] | undefined,
  threatClass: ThreatClass | undefined
): string {
  if (!threatClass || threatClass === 'NORMAL') {
    return 'Traffic metrics are within normal baseline ranges. No anomalies detected.';
  }

  if (!features || features.length === 0) {
    return `The system forecasted an elevated risk level of ${threatClass} based on current network telemetry.`;
  }

  const featureSummaries = features.map((f) => {
    const cleanName = formatFeatureName(f.name);
    return `${cleanName} (${f.actual_value})`;
  });

  return `The forecast was triggered primarily by a notable increase in ${featureSummaries.join(
    ', '
  )}.`;
}

// Simple severity styling
export function getSeverityStyle(threatClass: ThreatClass | undefined) {
  const normalized = (threatClass || 'NORMAL').toUpperCase();
  switch (normalized) {
    case 'IMMINENT':
      return {
        label: 'IMMINENT',
        textClass: 'text-red-400',
        bgClass: 'bg-red-500/10',
        borderClass: 'border-red-500/40',
        badgeBg: 'bg-red-500/20 text-red-300 border-red-500/30',
        barColor: '#ef4444',
      };
    case 'NEAR-TERM':
      return {
        label: 'NEAR-TERM',
        textClass: 'text-orange-400',
        bgClass: 'bg-orange-500/10',
        borderClass: 'border-orange-500/40',
        badgeBg: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
        barColor: '#f97316',
      };
    case 'ELEVATED':
      return {
        label: 'ELEVATED',
        textClass: 'text-amber-400',
        bgClass: 'bg-amber-500/10',
        borderClass: 'border-amber-500/40',
        badgeBg: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
        barColor: '#f59e0b',
      };
    case 'NORMAL':
    default:
      return {
        label: 'NORMAL',
        textClass: 'text-emerald-400',
        bgClass: 'bg-emerald-500/10',
        borderClass: 'border-emerald-500/30',
        badgeBg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
        barColor: '#10b981',
      };
  }
}

export function formatTimestamp(isoString?: string): string {
  if (!isoString) return '--:--:--';
  try {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return isoString;
  }
}