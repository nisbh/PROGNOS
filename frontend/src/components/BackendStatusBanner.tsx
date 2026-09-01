import React from 'react';
import { AlertCircle, Terminal } from 'lucide-react';
import { API_BASE_URL } from '../services/api';

interface BackendStatusBannerProps {
  errorMessage: string | null;
}

export const BackendStatusBanner: React.FC<BackendStatusBannerProps> = ({
  errorMessage,
}) => {
  return (
    <div className="w-full bg-red-950/30 border border-red-800/40 rounded-lg p-4 mb-6 text-sm">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
        <div className="flex-1">
          <h4 className="font-semibold text-red-300">
            Cannot Connect to Backend ({API_BASE_URL})
          </h4>
          <p className="text-xs text-slate-300 mt-1">
            {errorMessage || 'FastAPI server is not responding. Automatically retrying...'}
          </p>
          <div className="mt-2.5 flex items-center gap-2 text-xs text-slate-400">
            <Terminal className="w-3.5 h-3.5 text-sky-400" />
            <span>To start the backend server, run:</span>
            <code className="text-slate-200 bg-slate-900 px-2 py-0.5 rounded border border-slate-800 font-mono">
              python -m uvicorn backend.main:app --reload
            </code>
          </div>
        </div>
      </div>
    </div>
  );
};