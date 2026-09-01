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

export async function fetchHistory(limit: number = 60, baseUrl: string = API_BASE_URL): Promise<HistoryResponse> {
  const res = await fetchWithTimeout(`${baseUrl}/history?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch history (HTTP ${res.status})`);
  return res.json();
}

export async function uploadReplay(file: File, baseUrl: string = API_BASE_URL): Promise<{status: string, message: string}> {
  const formData = new FormData();
  formData.append('file', file);
  
  const res = await fetch(`${baseUrl}/upload-replay`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`Failed to upload replay (HTTP ${res.status})`);
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
      fetchHistory(60, baseUrl),
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

// Format risk score with a maximum of 2 decimal places (e.g. 14.7619 -> 14.76, 48.0 -> 48, 9.126 -> 9.13)
export function formatRiskScore(score?: number | null): string {
  if (score === undefined || score === null || isNaN(score)) return '0';
  const rounded = Math.round((score + Number.EPSILON) * 100) / 100;
  return rounded.toString();
}

// Format backend telemetry variable names into clean, readable Title Case without snake_case
export function formatFeatureName(rawName: string): string {
  if (!rawName) return '';

  // Direct specific mappings
  const knownMappings: Record<string, string> = {
    SYN_rate_slope: 'SYN Rate Slope',
    syn_rate_slope: 'SYN Rate Slope',
    unique_source_ips_pct_change: 'Unique Source IPs (% Change)',
    connection_count: 'Connection Count',
    connection_count_rolling_mean: 'Connection Count (Rolling Mean)',
    syn_rate_1m_avg: 'SYN Rate 1 Minute Average',
    connections_1m_avg: 'Connections 1 Minute Average',
    packet_size_1m_avg: 'Packet Size 1 Minute Average',
    flow_duration_mean: 'Flow Duration Mean',
  };

  if (knownMappings[rawName]) {
    return knownMappings[rawName];
  }

  // General humanization algorithm
  // 1. Replace underscores and hyphens with spaces
  let formatted = rawName.replace(/[_-]/g, ' ');

  // 2. Expand common abbreviations
  const abbreviationMap: Record<string, string> = {
    '1m': '1 Minute',
    '5m': '5 Minute',
    '10m': '10 Minute',
    '15m': '15 Minute',
    'avg': 'Average',
    'std': 'Std Dev',
    'pct': 'Percent',
    'ips': 'IPs',
    'syn': 'SYN',
    'tcp': 'TCP',
    'udp': 'UDP',
    'http': 'HTTP',
    'icmp': 'ICMP',
    'dos': 'DoS',
    'ddos': 'DDoS',
    'cnt': 'Count',
    'len': 'Length',
    'dur': 'Duration',
    'max': 'Max',
    'min': 'Min',
    'sec': 'Second',
  };

  // Split into words, apply token replacements, and capitalize
  const words = formatted.split(/\s+/).filter(Boolean);
  const transformedWords = words.map((word) => {
    const lower = word.toLowerCase();
    if (abbreviationMap[lower]) {
      return abbreviationMap[lower];
    }
    // Capitalize first letter
    return word.charAt(0).toUpperCase() + word.slice(1);
  });

  return transformedWords.join(' ');
}

// Generate simple plain-English explanation strictly based on actual backend features and values
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

// Explicitly sort traffic telemetry points ascending (oldest -> newest, left -> right)
export function getSortedTrafficHistory(traffic?: TrafficResponse | null): Array<{
  timestamp: string;
  connections_per_sec: number;
  syn_rate: number;
  time: string;
}> {
  if (!traffic?.history) return [];
  const sorted = [...traffic.history].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );
  return sorted.map((pt) => ({
    ...pt,
    time: formatTimestamp(pt.timestamp),
  }));
}

// Explicitly sort risk classification history ascending (oldest -> newest, left -> right)
export function getSortedRiskHistory(history?: HistoryResponse | null): Array<{
  ts: string;
  class: ThreatClass;
}> {
  if (!history?.history) return [];
  return [...history.history].sort(
    (a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime()
  );
}

// Sort risk history descending (newest -> oldest, top -> bottom for tables)
export function getHistoryNewestFirst(history?: HistoryResponse | null): Array<{
  ts: string;
  class: ThreatClass;
}> {
  if (!history?.history) return [];
  return [...history.history].sort(
    (a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime()
  );
}
