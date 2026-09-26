import React from 'react';
import { 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  Download, 
  ShieldCheck, 
  TrendingUp, 
  Database,
  ArrowLeft,
  Trash2
} from 'lucide-react';
import { AnalysisSession, AnalysisReport } from '../types';
import { PlotlyChart } from '../components/PlotlyChart';

interface ExecutiveReportProps {
  session: AnalysisSession | null;
  onBack: () => void;
  onDeleteSession?: (sessionId: string) => void;
}

export const ExecutiveReport: React.FC<ExecutiveReportProps> = ({ session, onBack, onDeleteSession }) => {
  if (!session || !session.finalReport) {
    return (
      <div className="glass-panel p-12 rounded-xl text-center max-w-3xl mx-auto space-y-4 animate-fadeIn border border-neutral-800">
        <div className="w-16 h-16 rounded-xl bg-neutral-900 border border-neutral-800 flex items-center justify-center text-white mx-auto">
          <FileText className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-white">No Executive Report Selected</h2>
        <p className="text-neutral-400 text-sm max-w-md mx-auto">
          Run an analysis in the Workspace or pick a session from the Dashboard to read the generated executive intelligence summary.
        </p>
        <button
          onClick={onBack}
          className="px-5 py-2.5 rounded-lg bg-white text-black font-bold text-xs inline-flex items-center space-x-2 transition-colors hover:bg-neutral-200"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Dashboard</span>
        </button>
      </div>
    );
  }

  const report: AnalysisReport = session.finalReport;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-5xl mx-auto pb-12">
      {/* Top Header Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-800">
        <button
          onClick={onBack}
          className="inline-flex items-center space-x-2 text-neutral-400 hover:text-white text-xs font-semibold transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </button>

        <div className="flex items-center space-x-3">
          {onDeleteSession && (
            <button
              onClick={() => {
                if (window.confirm(`Delete this analyzed report for "${session.userQuestion}"?`)) {
                  onDeleteSession(session._id);
                  onBack();
                }
              }}
              className="px-4 py-2 rounded-lg bg-neutral-900 hover:bg-red-950 text-neutral-300 hover:text-red-400 border border-neutral-700 hover:border-red-800 text-xs font-semibold flex items-center space-x-2 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Delete Analysis</span>
            </button>
          )}
          <button
            onClick={handlePrint}
            className="px-4 py-2 rounded-lg bg-neutral-900 hover:bg-neutral-800 text-white border border-neutral-700 text-xs font-semibold flex items-center space-x-2 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export / Print PDF</span>
          </button>
          <div className="px-3 py-1.5 rounded-lg bg-neutral-900 border border-neutral-700 text-white text-xs font-bold flex items-center space-x-1.5 font-mono">
            <ShieldCheck className="w-4 h-4 text-white" />
            <span>Verified Report</span>
          </div>
        </div>
      </div>

      {/* Report Hero Card */}
      <div className="glass-panel p-8 sm:p-10 rounded-xl border border-neutral-800 relative overflow-hidden">
        <div className="space-y-3 relative z-10">
          <div className="flex items-center space-x-2 text-neutral-400 text-xs font-mono uppercase tracking-wider font-semibold">
            <FileText className="w-4 h-4 text-white" />
            <span>Executive Analysis Report</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
            {report.title || "Executive Analysis Report"}
          </h1>
          <p className="text-neutral-300 text-sm sm:text-base font-medium">
            Objective: <span className="text-white font-mono italic">"{session.userQuestion}"</span>
          </p>

          <div className="pt-3 flex flex-wrap items-center gap-4 text-xs font-mono text-neutral-400">
            <span className="flex items-center space-x-1.5">
              <Database className="w-3.5 h-3.5 text-white" />
              <span>Dataset: {report.dataset_overview?.dataset_name || 'Active Data'}</span>
            </span>
            <span>•</span>
            <span>Shape: {report.dataset_overview?.row_count} rows × {report.dataset_overview?.col_count} columns</span>
            <span>•</span>
            <span className="text-white font-bold">Data Quality: {report.dataset_overview?.data_quality_score}/100</span>
          </div>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="glass-panel p-6 sm:p-8 rounded-xl border border-neutral-800 space-y-4">
        <div className="flex items-center space-x-2 text-white font-bold text-base">
          <FileText className="w-5 h-5 text-white" />
          <span>Executive Summary</span>
        </div>
        <p className="text-neutral-200 text-sm leading-relaxed whitespace-pre-line font-sans">
          {report.executive_summary}
        </p>
      </div>

      {/* Key Empirically Validated Findings */}
      <div className="glass-panel p-6 sm:p-8 rounded-xl border border-neutral-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-white font-bold text-base">
            <ShieldCheck className="w-5 h-5 text-white" />
            <span>Validated Findings & Empirical Evidence</span>
          </div>
          <span className="text-xs font-mono text-neutral-300 bg-neutral-900 px-2.5 py-1 rounded border border-neutral-700">
            Cross-Validated Data
          </span>
        </div>

        <div className="grid grid-cols-1 gap-3">
          {report.key_findings?.map((finding, idx) => (
            <div key={idx} className="p-4 rounded-lg bg-black border border-neutral-800 flex items-start space-x-3">
              <div className="w-6 h-6 rounded bg-neutral-800 text-white flex items-center justify-center font-bold text-xs flex-shrink-0 mt-0.5 border border-neutral-700">
                {idx + 1}
              </div>
              <p className="text-sm text-neutral-200 leading-relaxed font-sans">{finding}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Visual Insights & Charts */}
      {report.visual_insights && report.visual_insights.length > 0 && (
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-white" />
            <span>Interactive Visual Evidence</span>
          </h2>

          <div className="grid grid-cols-1 gap-6">
            {report.visual_insights.map((viz, idx) => (
              <div key={idx} className="glass-panel p-6 rounded-xl border border-neutral-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-white">{viz.title}</h3>
                  <span className="text-xs font-mono uppercase bg-neutral-900 text-neutral-400 border border-neutral-800 px-2.5 py-1 rounded">
                    {viz.chart_type}
                  </span>
                </div>
                <PlotlyChart spec={viz.chart_spec} height={380} />
                <p className="text-xs text-neutral-400 italic pt-2 border-t border-neutral-800">
                  {viz.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Machine Learning Model Results if available */}
      {report.ml_results && (
        <div className="glass-panel p-6 sm:p-8 rounded-xl border border-neutral-800 space-y-4">
          <div className="flex items-center space-x-2 text-white font-bold text-base">
            <TrendingUp className="w-5 h-5 text-white" />
            <span>Machine Learning & Algorithmic Results</span>
          </div>

          <div className="p-4 rounded-lg bg-black border border-neutral-800 font-mono text-xs space-y-2">
            <div className="text-neutral-200 font-semibold">
              Model Type: {report.ml_results.model_type || 'Supervised / Clustering Model'}
            </div>
            {report.ml_results.metrics && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                {Object.entries(report.ml_results.metrics).map(([k, v]: [string, any]) => (
                  <div key={k} className="p-2.5 rounded bg-neutral-900 border border-neutral-800">
                    <div className="text-[10px] uppercase text-neutral-400">{k}</div>
                    <div className="text-base font-bold text-white mt-0.5">
                      {typeof v === 'number' ? v.toFixed(3) : String(v)}
                    </div>
                  </div>
                ))}
              </div>
            )}
            {report.ml_results.feature_importance && (
              <div className="pt-2">
                <div className="text-neutral-400 text-xs mb-1">Top Predictive Features:</div>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(report.ml_results.feature_importance)
                    .sort((a: any, b: any) => b[1] - a[1])
                    .slice(0, 5)
                    .map(([feat, score]: [string, any]) => (
                      <span key={feat} className="px-2.5 py-1 rounded bg-neutral-900 text-neutral-200 border border-neutral-800">
                        {feat}: {(score * 100).toFixed(1)}%
                      </span>
                    ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Strategic Recommendations */}
      {report.recommendations && report.recommendations.length > 0 && (
        <div className="glass-panel p-6 sm:p-8 rounded-xl border border-neutral-800 space-y-4">
          <div className="flex items-center space-x-2 text-white font-bold text-base">
            <CheckCircle2 className="w-5 h-5 text-white" />
            <span>Actionable Strategic Recommendations</span>
          </div>
          <div className="space-y-3">
            {report.recommendations.map((rec, i) => (
              <div key={i} className="p-4 rounded-lg bg-black border border-neutral-800 flex items-start space-x-3">
                <div className="w-5 h-5 rounded-full bg-white text-black flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                  ✓
                </div>
                <p className="text-sm text-neutral-200 leading-relaxed font-sans">{rec}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Limitations & Caveats */}
      {report.limitations && report.limitations.length > 0 && (
        <div className="glass-panel p-6 sm:p-8 rounded-xl border border-neutral-800 space-y-4">
          <div className="flex items-center space-x-2 text-neutral-300 font-bold text-base">
            <AlertTriangle className="w-5 h-5 text-white" />
            <span>Methodological Limitations & Caveats</span>
          </div>
          <div className="space-y-2">
            {report.limitations.map((lim, i) => (
              <div key={i} className="text-xs text-neutral-300 font-sans flex items-start space-x-2">
                <span className="text-white font-mono">•</span>
                <span>{lim}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

