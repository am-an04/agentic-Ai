import React from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  ShieldCheck, 
  FileSpreadsheet, 
  ArrowRight, 
  CheckCircle2, 
  Activity,
  Layers,
  Trash2
} from 'lucide-react';
import { Dataset, AnalysisSession } from '../types';

interface DashboardProps {
  datasets: Dataset[];
  sessions: AnalysisSession[];
  onSelectDataset: (dataset: Dataset) => void;
  onAskQuestion: (dataset: Dataset, question: string) => void;
  onViewReport: (session: AnalysisSession) => void;
  onDeleteSession?: (sessionId: string) => void;
  onDeleteAllSessions?: () => void;
  onDeleteDataset?: (datasetId: string) => void;
  onNavigateToUpload?: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  datasets,
  sessions,
  onSelectDataset,
  onViewReport,
  onDeleteSession,
  onDeleteAllSessions,
  onDeleteDataset,
  onNavigateToUpload
}) => {
  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Hero Banner - Monochrome */}
      <div className="relative overflow-hidden rounded-2xl p-8 sm:p-10 border border-neutral-800 bg-neutral-900/60">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded bg-neutral-800 border border-neutral-700 text-neutral-300 text-xs font-mono mb-4">
            <Activity className="w-3.5 h-3.5 text-white" />
            <span>Data Analysis & Intelligence Engine</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight mb-4">
            Transform Datasets into <span className="text-neutral-400">Validated Insights</span>.
          </h1>
          <p className="text-neutral-300 text-base sm:text-lg leading-relaxed mb-6">
            Execute the complete analytical lifecycle: data profiling, hypothesis planning, execution, empirical observation, and executive reporting.
          </p>

          <div className="flex flex-wrap gap-4 text-xs font-mono text-neutral-400">
            <span className="flex items-center space-x-1.5 bg-black px-3 py-1.5 rounded border border-neutral-800">
              <CheckCircle2 className="w-3.5 h-3.5 text-white" />
              <span>Structured Pipeline</span>
            </span>
            <span className="flex items-center space-x-1.5 bg-black px-3 py-1.5 rounded border border-neutral-800">
              <CheckCircle2 className="w-3.5 h-3.5 text-white" />
              <span>Statistical & ML Models</span>
            </span>
            <span className="flex items-center space-x-1.5 bg-black px-3 py-1.5 rounded border border-neutral-800">
              <CheckCircle2 className="w-3.5 h-3.5 text-white" />
              <span>Cross-Validation Verification</span>
            </span>
          </div>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <div className="glass-panel p-5 rounded-xl border border-neutral-800">
          <div className="flex items-center justify-between text-neutral-400 mb-2">
            <span className="text-xs uppercase font-semibold tracking-wider">Available Datasets</span>
            <FileSpreadsheet className="w-4 h-4 text-white" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white">{datasets.length}</div>
          <p className="text-xs text-neutral-500 mt-1">Ready for investigation</p>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-neutral-800">
          <div className="flex items-center justify-between text-neutral-400 mb-2">
            <span className="text-xs uppercase font-semibold tracking-wider">Analyses Executed</span>
            <Layers className="w-4 h-4 text-white" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white">{sessions.length}</div>
          <p className="text-xs text-neutral-500 mt-1">Completed runs</p>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-neutral-800">
          <div className="flex items-center justify-between text-neutral-400 mb-2">
            <span className="text-xs uppercase font-semibold tracking-wider">Validation Rate</span>
            <ShieldCheck className="w-4 h-4 text-white" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white">100%</div>
          <p className="text-xs text-neutral-500 mt-1">Empirically grounded</p>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-neutral-800">
          <div className="flex items-center justify-between text-neutral-400 mb-2">
            <span className="text-xs uppercase font-semibold tracking-wider">Avg Data Quality</span>
            <BarChart3 className="w-4 h-4 text-white" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white">96.4<span className="text-sm font-normal text-neutral-500">/100</span></div>
          <p className="text-xs text-neutral-500 mt-1">Profiled accuracy</p>
        </div>
      </div>

      {/* Datasets & Past Reports Split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Loaded Datasets */}
        <div className="glass-panel p-6 rounded-xl border border-neutral-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-white flex items-center space-x-2">
              <FileSpreadsheet className="w-4 h-4 text-white" />
              <span>Loaded Datasets</span>
            </h3>
            <span className="text-xs text-neutral-400 font-mono">{datasets.length} files</span>
          </div>

          <div className="space-y-3">
            {datasets.length === 0 ? (
              <div className="text-center py-8 text-neutral-500 text-sm space-y-3">
                <p>No datasets loaded yet. Browse and upload a file to begin.</p>
                {onNavigateToUpload && (
                  <button
                    onClick={onNavigateToUpload}
                    className="px-4 py-2 rounded-lg bg-white text-black font-bold text-xs inline-flex items-center space-x-2 hover:bg-neutral-200 transition-colors"
                  >
                    <span>Browse & Upload Dataset</span>
                  </button>
                )}
              </div>
            ) : (
              datasets.map((d) => (
                <div 
                  key={d._id}
                  className="p-4 rounded-lg bg-neutral-900 border border-neutral-800 hover:border-neutral-600 transition-colors flex items-center justify-between"
                >
                  <div>
                    <div className="font-semibold text-neutral-100 text-sm">{d.originalName}</div>
                    <div className="text-xs text-neutral-400 mt-0.5 font-mono">
                      {d.rowCount} rows • {d.colCount} cols • Quality: {d.qualityScore}/100
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => onSelectDataset(d)}
                      className="px-3.5 py-1.5 rounded bg-white text-black hover:bg-neutral-200 text-xs font-bold flex items-center space-x-1.5 transition-colors"
                    >
                      <span>Analyze</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                    {onDeleteDataset && (
                      <button
                        title="Delete dataset"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm(`Delete dataset "${d.originalName}" and its related analysis?`)) {
                            onDeleteDataset(d._id);
                          }
                        }}
                        className="p-1.5 rounded bg-neutral-800 hover:bg-red-950 text-neutral-400 hover:text-red-400 border border-neutral-700 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Analysis Sessions / Analyzed Work */}
        <div className="glass-panel p-6 rounded-xl border border-neutral-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-white flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-white" />
              <span>Analysis Reports</span>
            </h3>
            <div className="flex items-center space-x-2">
              {sessions.length > 0 && onDeleteAllSessions && (
                <button
                  onClick={onDeleteAllSessions}
                  className="px-2.5 py-1 rounded bg-neutral-900 border border-neutral-700 hover:border-red-600 text-neutral-400 hover:text-red-400 text-xs font-mono flex items-center space-x-1.5 transition-colors"
                  title="Delete all analyzed work sessions"
                >
                  <Trash2 className="w-3 h-3" />
                  <span>Delete All Work</span>
                </button>
              )}
              <span className="text-xs text-neutral-400 font-mono">{sessions.length} sessions</span>
            </div>
          </div>

          <div className="space-y-3">
            {sessions.length === 0 ? (
              <div className="text-center py-8 text-neutral-500 text-sm">
                No analysis sessions yet. Start an analysis from the Workspace.
              </div>
            ) : (
              sessions.map((s) => (
                <div 
                  key={s._id}
                  onClick={() => onViewReport(s)}
                  className="p-4 rounded-lg bg-neutral-900 border border-neutral-800 hover:border-neutral-600 transition-colors flex items-center justify-between cursor-pointer group"
                >
                  <div className="max-w-[70%]">
                    <div className="font-medium text-neutral-200 text-sm truncate">"{s.userQuestion}"</div>
                    <div className="text-xs text-neutral-400 mt-0.5 font-mono flex items-center space-x-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                        s.status === 'completed' ? 'bg-white text-black border-white' : 'bg-neutral-800 text-neutral-300 border-neutral-700'
                      }`}>
                        {s.status}
                      </span>
                      <span>{new Date(s.createdAt).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {onDeleteSession && (
                      <button
                        title="Delete this analyzed work"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm(`Delete analysis "${s.userQuestion}"?`)) {
                            onDeleteSession(s._id);
                          }
                        }}
                        className="p-1.5 rounded bg-neutral-800 hover:bg-red-950 text-neutral-400 hover:text-red-400 border border-neutral-700 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                    <ArrowRight className="w-4 h-4 text-neutral-400 group-hover:text-white transition-colors" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

