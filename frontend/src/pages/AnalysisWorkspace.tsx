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
  Trash2,
  Cpu,
  Zap,
  BookOpen,
  ListChecks
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
            <option value="">Select a dataset...</option>
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
          {/* Left Column: Autonomous Plan & Execution Log */}
          <div className="lg:col-span-5 space-y-4">
            {/* Autonomous Plan Card if present */}
            {session.plan && (
              <div className="glass-panel p-5 rounded-xl space-y-3 border border-neutral-800">
                <div className="flex items-center justify-between pb-2 border-b border-neutral-800">
                  <div className="flex items-center space-x-2 text-white font-bold text-sm">
                    <ListChecks className="w-4 h-4 text-white" />
                    <span>Autonomous Plan</span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-neutral-900 border border-neutral-700 text-neutral-300">
                    {session.plan.plan_steps?.length || 0} Steps
                  </span>
                </div>

                {session.plan.reasoning && (
                  <div className="p-3 rounded-lg bg-black border border-neutral-800 space-y-1">
                    <div className="text-[10px] font-mono uppercase text-neutral-400 font-semibold flex items-center space-x-1">
                      <Sparkles className="w-3 h-3 text-white" />
                      <span>Planner Reasoning</span>
                    </div>
                    <p className="text-xs text-neutral-300 font-sans leading-relaxed italic">
                      "{session.plan.reasoning}"
                    </p>
                  </div>
                )}

                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {session.plan.plan_steps?.map((step: any, idx: number) => (
                    <div key={idx} className="p-2.5 rounded bg-black border border-neutral-850 flex items-center justify-between text-xs font-mono">
                      <div className="flex items-center space-x-2 truncate">
                        <span className="text-neutral-500 font-bold">#{step.step_number || idx + 1}</span>
                        <span className="text-neutral-200 truncate">{step.action}</span>
                      </div>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-semibold flex-shrink-0 ${
                        step.status === 'completed' ? 'bg-neutral-900 text-neutral-300 border border-neutral-800' :
                        step.status === 'failed' ? 'bg-neutral-900 text-red-400 border border-neutral-800' :
                        step.status === 'running' ? 'bg-white text-black font-bold' :
                        'bg-neutral-950 text-neutral-500 border border-neutral-850'
                      }`}>
                        {step.status || 'pending'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Execution Log */}
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
                  <div key={idx} className="p-3 rounded-lg bg-black border border-neutral-800 space-y-1.5">
                    <div className="flex items-center justify-between text-white font-semibold">
                      <span>{log.step}</span>
                      <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                    </div>
                    <p className="text-neutral-400 font-sans text-xs">{log.description}</p>
                    
                    {/* LLM Usage Telemetry Badge */}
                    {log.llm_usage && (
                      <div className="pt-1 flex flex-wrap items-center gap-1.5 text-[10px] text-neutral-400">
                        <span className="px-1.5 py-0.5 rounded bg-neutral-900 border border-neutral-800 text-neutral-300 font-mono flex items-center space-x-1">
                          <Cpu className="w-2.5 h-2.5 text-white" />
                          <span>{log.llm_usage.model || 'llm'}</span>
                        </span>
                        {log.llm_usage.total_tokens !== undefined && (
                          <span className="px-1.5 py-0.5 rounded bg-neutral-900 border border-neutral-800 font-mono">
                            {log.llm_usage.total_tokens} tokens
                          </span>
                        )}
                        {log.llm_usage.latency_ms !== undefined && (
                          <span className="px-1.5 py-0.5 rounded bg-neutral-900 border border-neutral-800 font-mono">
                            {log.llm_usage.latency_ms.toFixed(0)}ms
                          </span>
                        )}
                        {log.llm_usage.estimated_cost_usd !== undefined && log.llm_usage.estimated_cost_usd > 0 && (
                          <span className="px-1.5 py-0.5 rounded bg-neutral-900 border border-neutral-800 font-mono text-neutral-300">
                            ${log.llm_usage.estimated_cost_usd.toFixed(6)}
                          </span>
                        )}
                      </div>
                    )}
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

