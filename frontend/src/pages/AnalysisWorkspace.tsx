import React, { useState } from 'react';
import { 
  Send, 
  Terminal, 
  CheckCircle2, 
  AlertCircle, 
  ShieldCheck, 
  BarChart2, 
  FileText, 
  ArrowRight,
  UserCheck,
  Search,
  Activity,
  Sparkles,
  Trash2
} from 'lucide-react';
import { Dataset, AnalysisSession } from '../types';
import { api } from '../services/api';
import { PlotlyChart } from '../components/PlotlyChart';

interface AnalysisWorkspaceProps {
  activeDataset: Dataset | null;
  datasets: Dataset[];
  onSelectDataset: (dataset: Dataset) => void;
  initialQuestion?: string;
  onViewReport: (session: AnalysisSession) => void;
  onDeleteSession?: (sessionId: string) => void;
}

export const AnalysisWorkspace: React.FC<AnalysisWorkspaceProps> = ({
  activeDataset,
  datasets,
  onSelectDataset,
  initialQuestion = '',
  onViewReport,
  onDeleteSession
}) => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [session, setSession] = useState<AnalysisSession | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleStartAnalysis = async () => {
    if (!activeDataset) {
      setError("Please select a dataset first.");
      return;
    }
    if (!question.trim()) {
      setError("Please enter an analytical question.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.startAnalysis(activeDataset._id, question.trim());
      setSession(res.session);
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || "Failed to execute analysis.");
    } finally {
      setLoading(false);
    }
  };

  const handleHumanApproval = async (approved: boolean) => {
    if (!session) return;
    setLoading(true);
    try {
      const res = await api.approveAction(session._id, approved);
      setSession(res.session);
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || "Failed to submit approval.");
    } finally {
      setLoading(false);
    }
  };

  const getDefaultQuestions = (): string[] => {
    if (!activeDataset) {
      return [
        "Analyze statistical correlations, distributions, and outliers across the uploaded dataset.",
        "Perform regression or classification to model primary relationships and key metrics."
      ];
    }
    const cols = activeDataset.columns || [];
    const numCols = activeDataset.numericalColumns || [];
    if (numCols.length >= 2) {
      return [
        `Analyze correlations and distributions between ${numCols[0]} and ${numCols[1]} in ${activeDataset.originalName}.`,
        `Identify significant drivers and anomalies affecting ${numCols[0]} in this dataset.`
      ];
    }
    if (cols.length > 0) {
      return [
        `Analyze distributions and key statistical patterns across all features in ${activeDataset.originalName}.`,
        `Detect anomalous records and build a predictive summary model for ${activeDataset.originalName}.`
      ];
    }
    return [
      `Analyze statistical correlations, distributions, and outliers in ${activeDataset.originalName}.`,
      `Build a predictive model to identify key factors and patterns in ${activeDataset.originalName}.`
    ];
  };

  const defaultQuestions = getDefaultQuestions();

  const handleDeleteCurrentSession = async () => {
    if (!session) return;
    if (window.confirm("Are you sure you want to delete this analyzed work?")) {
      if (onDeleteSession) {
        onDeleteSession(session._id);
      } else {
        try {
          await api.deleteSession(session._id);
        } catch (_) {}
      }
      setSession(null);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn max-w-7xl mx-auto">
      {/* Top Dataset Selector Banner */}
      <div className="glass-panel p-4 sm:p-5 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 border border-neutral-800">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-neutral-900 border border-neutral-800 flex items-center justify-center text-white">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-neutral-400 uppercase font-mono tracking-wider">Active Dataset</div>
            <div className="text-base font-bold text-white flex items-center space-x-2">
              <span>{activeDataset ? activeDataset.originalName : "No dataset selected"}</span>
              {activeDataset && (
                <span className="text-xs font-mono font-normal text-neutral-400">
                  ({activeDataset.rowCount} rows • {activeDataset.colCount} cols)
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={activeDataset?._id || ''}
            onChange={(e) => {
              const d = datasets.find(item => item._id === e.target.value);
              if (d) onSelectDataset(d);
            }}
            className="bg-neutral-900 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-2 font-mono focus:outline-none focus:border-white"
          >
            {datasets.map(d => (
              <option key={d._id} value={d._id}>{d.originalName}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Analytical Question Input Box */}
      <div className="glass-panel p-6 rounded-xl border border-neutral-800 shadow-xl relative overflow-hidden">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-mono uppercase tracking-wider text-neutral-300 flex items-center space-x-2">
              <Search className="w-4 h-4 text-white" />
              <span>Analytical Query</span>
            </label>
            <span className="text-[11px] font-mono text-neutral-500">Press Enter or click Run to analyze</span>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Enter analytical question or query..."
              disabled={loading}
              onKeyDown={(e) => e.key === 'Enter' && !loading && handleStartAnalysis()}
              className="flex-1 bg-black border border-neutral-800 rounded-lg px-4 py-3 text-white placeholder-neutral-500 text-sm focus:outline-none focus:border-white focus:ring-1 focus:ring-white transition-all font-sans"
            />
            <button
              onClick={handleStartAnalysis}
              disabled={loading || !question.trim()}
              className="px-6 py-3 rounded-lg bg-white text-black font-bold text-sm hover:bg-neutral-200 flex items-center justify-center space-x-2 disabled:opacity-40 transition-colors"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <span>Run Analysis</span>
                  <Send className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          {/* Quick Query Presets */}
          <div className="pt-2 flex flex-col sm:flex-row items-start sm:items-center gap-2 text-xs">
            <span className="text-neutral-400 font-mono flex items-center space-x-1.5 flex-shrink-0">
              <Sparkles className="w-3.5 h-3.5 text-white" />
              <span>Suggested Queries:</span>
            </span>
            <div className="flex flex-wrap gap-2">
              {defaultQuestions.map((defQ, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setQuestion(defQ)}
                  className="px-3 py-1.5 rounded-lg bg-neutral-900 border border-neutral-700 hover:border-white text-neutral-300 hover:text-white text-xs font-sans text-left transition-colors flex items-center space-x-1.5"
                  title="Click to populate with this default value"
                >
                  <span className="font-mono text-neutral-500 font-bold">#{idx + 1}</span>
                  <span className="line-clamp-1">{defQ}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-neutral-900 border border-neutral-700 text-neutral-200 text-sm flex items-center space-x-2 animate-fadeIn">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-white" />
          <span>{error}</span>
        </div>
      )}

      {/* Decision Point Confirmation Banner */}
      {session && session.status === 'approval_required' && (
        <div className="glass-panel border border-neutral-600 bg-neutral-900/90 p-6 rounded-xl space-y-4">
          <div className="flex items-start space-x-3">
            <div className="w-10 h-10 rounded-lg bg-white text-black flex items-center justify-center flex-shrink-0">
              <UserCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="text-xs uppercase font-mono tracking-wider font-bold text-neutral-300">
                User Confirmation Required
              </div>
              <p className="text-white text-base font-semibold mt-1">
                {session.approvalPrompt || "Model training is requested for this analysis. Proceed with model execution?"}
              </p>
              <p className="text-xs text-neutral-400 mt-1">
                Confirm execution to proceed with full statistical and machine learning model fitting.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3 pt-2">
            <button
              onClick={() => handleHumanApproval(true)}
              disabled={loading}
              className="px-5 py-2.5 rounded-lg bg-white text-black font-bold text-xs hover:bg-neutral-200 transition-colors flex items-center space-x-1.5"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Confirm & Proceed</span>
            </button>
            <button
              onClick={() => handleHumanApproval(false)}
              disabled={loading}
              className="px-5 py-2.5 rounded-lg bg-neutral-800 text-neutral-300 font-semibold text-xs border border-neutral-700 hover:bg-neutral-700 transition-colors"
            >
              <span>Skip & Generate Report</span>
            </button>
          </div>
        </div>
      )}

      {/* Workspace Split: Execution Log vs Charts/Findings */}
      {session && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-fadeIn">
          {/* Analysis Execution Steps */}
          <div className="lg:col-span-5 space-y-4">
            <div className="glass-panel p-5 rounded-xl space-y-4 border border-neutral-800">
              <div className="flex items-center justify-between pb-3 border-b border-neutral-800">
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-white" />
                  <span className="font-bold text-white text-sm">Execution Log</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold bg-neutral-800 text-neutral-200 border border-neutral-700">
                    {session.status}
                  </span>
                  <button
                    onClick={handleDeleteCurrentSession}
                    title="Delete / Discard this analyzed work"
                    className="p-1 rounded bg-neutral-900 border border-neutral-700 hover:border-red-600 text-neutral-400 hover:text-red-400 text-xs transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Log steps */}
              <div className="space-y-3 font-mono text-xs max-h-[550px] overflow-y-auto pr-1">
                {session.traceLogs?.map((log, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-black border border-neutral-800 space-y-1">
                    <div className="flex items-center justify-between text-white font-semibold">
                      <span>{log.step}</span>
                      <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                    </div>
                    <p className="text-neutral-400 font-sans text-xs">{log.description}</p>
                  </div>
                ))}
              </div>

              {session.finalReport && (
                <button
                  onClick={() => onViewReport(session)}
                  className="w-full py-3 rounded-lg bg-white text-black font-bold text-xs hover:bg-neutral-200 flex items-center justify-center space-x-2 transition-colors mt-4"
                >
                  <FileText className="w-4 h-4" />
                  <span>View Executive Report</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Visualization & Empirical Findings */}
          <div className="lg:col-span-7 space-y-6">
            {/* Visual Insights Section */}
            {session.finalReport?.visual_insights && session.finalReport.visual_insights.length > 0 && (
              <div className="glass-panel p-6 rounded-xl border border-neutral-800 space-y-4">
                <div className="flex items-center space-x-2 text-white font-bold text-sm">
                  <BarChart2 className="w-4 h-4 text-white" />
                  <span>Empirical Visualizations</span>
                </div>
                {session.finalReport.visual_insights.map((viz, i) => (
                  <div key={i} className="space-y-2">
                    <h4 className="text-xs font-semibold text-neutral-300">{viz.title}</h4>
                    <PlotlyChart spec={viz.chart_spec} height={360} />
                    <p className="text-xs text-neutral-400 italic">{viz.description}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Validated Key Findings */}
            {session.finalReport?.key_findings && (
              <div className="glass-panel p-6 rounded-xl border border-neutral-800 space-y-4">
                <div className="flex items-center space-x-2 text-white font-bold text-sm">
                  <ShieldCheck className="w-4 h-4 text-white" />
                  <span>Verified Findings & Evidence</span>
                </div>
                <div className="space-y-2">
                  {session.finalReport.key_findings.map((finding, idx) => (
                    <div key={idx} className="p-3 rounded-lg bg-black border border-neutral-800 flex items-start space-x-2.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-white mt-1.5 flex-shrink-0" />
                      <p className="text-xs text-neutral-200 leading-relaxed">{finding}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

