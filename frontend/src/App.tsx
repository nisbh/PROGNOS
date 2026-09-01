import { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopHeader } from './components/TopHeader';
import { DashboardPage } from './components/DashboardPage';
import { ThreatContextPage } from './components/ThreatContextPage';
import { BackendStatusBanner } from './components/BackendStatusBanner';
import type { DashboardData, ActiveTab } from './types/dashboard';
import { fetchAllDashboardData, API_BASE_URL } from './services/api';
import { Shield } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('dashboard');

  const [dashboardData, setDashboardData] = useState<DashboardData>({
    currentStatus: null,
    forecast: null,
    traffic: null,
    explanation: null,
    history: null,
  });

  const [backendOnline, setBackendOnline] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Polling fetcher
  const loadData = useCallback(async () => {
    const result = await fetchAllDashboardData(API_BASE_URL);

    if (result.error) {
      setBackendOnline(false);
      setErrorMessage(result.error);
    } else {
      setDashboardData(result.data);
      setBackendOnline(true);
      setErrorMessage(null);
    }
  }, []);

  // Initial fetch and 3-second polling interval
  useEffect(() => {
    let isMounted = true;

    const executeFetch = async () => {
      if (isMounted) {
        await loadData();
      }
    };

    executeFetch();

    const interval = setInterval(() => {
      executeFetch();
    }, 3000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [loadData]);

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-row font-sans">
      {/* 1. Fixed Left Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        backendOnline={backendOnline}
      />

      {/* 2. Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        {/* Minimal Top Header */}
        <TopHeader
          activeTab={activeTab}
          backendOnline={backendOnline}
        />

        {/* Scrollable Page Body */}
        <main className="flex-1 p-6 lg:p-8 flex flex-col">
          {/* Backend Offline Notice */}
          {!backendOnline && (
            <BackendStatusBanner errorMessage={errorMessage} />
          )}

          {/* Page Routing */}
          {activeTab === 'dashboard' && (
            <DashboardPage data={dashboardData} />
          )}

          {activeTab === 'threat-context' && (
            <ThreatContextPage data={dashboardData} />
          )}
        </main>

        {/* Minimal Footer */}
        <footer className="w-full bg-[#0d1322] border-t border-slate-800/80 py-3.5 px-6 lg:px-8 mt-auto">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
            <div className="flex items-center gap-2">
              <Shield className="w-3.5 h-3.5 text-sky-400" />
              <span className="text-slate-400 font-medium">PROGNOS</span>
              <span>• AI Network Attack Forecasting</span>
            </div>
            <span>Smart India Hackathon (SIH 2026)</span>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;
