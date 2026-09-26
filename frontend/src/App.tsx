import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { DatasetUpload } from './pages/DatasetUpload';
import { AnalysisWorkspace } from './pages/AnalysisWorkspace';
import { ExecutiveReport } from './pages/ExecutiveReport';
import { Dataset, AnalysisSession } from './types';
import { api } from './services/api';
import { AlertCircle, RefreshCw, BarChart3, Database } from 'lucide-react';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [sessions, setSessions] = useState<AnalysisSession[]>([]);
  const [activeDataset, setActiveDataset] = useState<Dataset | null>(null);
  const [activeSession, setActiveSession] = useState<AnalysisSession | null>(null);
  const [initialQuestion, setInitialQuestion] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [backendError, setBackendError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setBackendError(null);
      const [fetchedDatasets, fetchedSessions] = await Promise.all([
        api.listDatasets().catch(() => []),
        api.listSessions().catch(() => [])
      ]);
      setDatasets(fetchedDatasets);
      setSessions(fetchedSessions);
      if (fetchedDatasets.length > 0 && !activeDataset) {
        setActiveDataset(fetchedDatasets[0]);
      }
    } catch (err: any) {
      setBackendError("Could not connect to backend gateway. Ensure server processes are active.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectDataset = (dataset: Dataset) => {
    setActiveDataset(dataset);
    setCurrentTab('workspace');
  };

  const handleAskQuestion = (dataset: Dataset, question: string) => {
    setActiveDataset(dataset);
    setInitialQuestion('');
    setCurrentTab('workspace');
  };

  const handleViewReport = (session: AnalysisSession) => {
    setActiveSession(session);
    setCurrentTab('reports');
  };

  const handleDatasetUploaded = (dataset: Dataset) => {
    setDatasets(prev => [dataset, ...prev]);
    setActiveDataset(dataset);
  };

  const handleProceedToWorkspace = (dataset: Dataset) => {
    setActiveDataset(dataset);
    setCurrentTab('workspace');
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await api.deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s._id !== sessionId));
      if (activeSession?._id === sessionId) {
        setActiveSession(null);
      }
    } catch (err: any) {
      alert("Failed to delete session: " + (err.response?.data?.error || err.message));
    }
  };

  const handleDeleteAllSessions = async () => {
    if (!window.confirm("Are you sure you want to delete all analyzed work and reports?")) return;
    try {
      await api.deleteAllSessions();
      setSessions([]);
      setActiveSession(null);
    } catch (err: any) {
      alert("Failed to delete all sessions: " + (err.response?.data?.error || err.message));
    }
  };

  const handleDeleteDataset = async (datasetId: string) => {
    try {
      await api.deleteDataset(datasetId);
      setDatasets(prev => prev.filter(d => d._id !== datasetId));
      setSessions(prev => prev.filter(s => {
        const id = typeof s.datasetId === 'object' && s.datasetId ? (s.datasetId as any)._id : s.datasetId;
        return id !== datasetId;
      }));
      if (activeDataset?._id === datasetId) {
        setActiveDataset(null);
      }
    } catch (err: any) {
      alert("Failed to delete dataset: " + (err.response?.data?.error || err.message));
    }
  };

  return (
    <div className="min-h-screen bg-black text-neutral-100 flex flex-col selection:bg-white selection:text-black">
      {/* Sticky Navigation */}
      <Navbar currentTab={currentTab} setCurrentTab={setCurrentTab} />

      {/* Backend Alert if offline */}
      {backendError && (
        <div className="bg-neutral-900 border-b border-neutral-800 px-4 py-2.5 text-xs text-neutral-300 flex items-center justify-between max-w-7xl mx-auto w-full">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-white flex-shrink-0" />
            <span>{backendError}</span>
          </div>
          <button
            onClick={loadData}
            className="flex items-center space-x-1 px-2.5 py-1 rounded bg-neutral-800 hover:bg-neutral-700 text-white transition-colors font-mono border border-neutral-700 text-xs"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
            <div className="w-10 h-10 rounded-xl bg-neutral-900 border border-neutral-800 flex items-center justify-center animate-spin text-white">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div className="text-xs font-mono text-neutral-400">Loading DataPilot workspace...</div>
          </div>
        ) : (
          <>
            {currentTab === 'dashboard' && (
              <Dashboard
                datasets={datasets}
                sessions={sessions}
                onSelectDataset={handleSelectDataset}
                onAskQuestion={handleAskQuestion}
                onViewReport={handleViewReport}
                onDeleteSession={handleDeleteSession}
                onDeleteAllSessions={handleDeleteAllSessions}
                onDeleteDataset={handleDeleteDataset}
                onNavigateToUpload={() => setCurrentTab('upload')}
              />
            )}

            {currentTab === 'upload' && (
              <DatasetUpload
                onDatasetUploaded={handleDatasetUploaded}
                onProceedToWorkspace={handleProceedToWorkspace}
              />
            )}

            {currentTab === 'workspace' && (
              <AnalysisWorkspace
                activeDataset={activeDataset}
                datasets={datasets}
                onSelectDataset={setActiveDataset}
                initialQuestion=""
                onViewReport={handleViewReport}
                onDeleteSession={handleDeleteSession}
              />
            )}

            {currentTab === 'reports' && (
              <ExecutiveReport
                session={activeSession || (sessions.length > 0 ? sessions[0] : null)}
                onBack={() => setCurrentTab('dashboard')}
                onDeleteSession={handleDeleteSession}
              />
            )}
          </>
        )}
      </main>

      {/* Modern Monochrome Status Footer */}
      <footer className="border-t border-neutral-800 py-6 bg-black text-xs text-neutral-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-white" />
            <span className="text-neutral-300 font-sans font-semibold">DataPilot Intelligence Platform</span>
            <span>•</span>
            <span>v1.0.0</span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-white" />
              <span>Analysis Service :8000</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-neutral-400" />
              <span>API Gateway :5000</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-neutral-600" />
              <span>Web Client :3000</span>
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;

