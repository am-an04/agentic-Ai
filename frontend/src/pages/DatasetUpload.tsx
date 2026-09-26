import React, { useState } from 'react';
import { UploadCloud, FileSpreadsheet, ArrowRight, AlertTriangle } from 'lucide-react';
import { Dataset } from '../types';
import { api } from '../services/api';

interface DatasetUploadProps {
  onDatasetUploaded: (dataset: Dataset) => void;
  onProceedToWorkspace: (dataset: Dataset) => void;
}

export const DatasetUpload: React.FC<DatasetUploadProps> = ({
  onDatasetUploaded,
  onProceedToWorkspace
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = async (file: File) => {
    if (!file.name.match(/\.(csv|xlsx|xls)$/i)) {
      setError("Only CSV and XLSX files are supported.");
      return;
    }

    setUploading(true);
    setError(null);
    try {
      const res = await api.uploadDataset(file);
      setSelectedDataset(res.dataset);
      onDatasetUploaded(res.dataset);
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || "Failed to upload dataset.");
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Dataset Ingestion & Profiling</h1>
        <p className="text-neutral-400 text-sm mt-1">
          Upload CSV or Excel data files to profile columnar structure, data types, missingness, and quality metrics.
        </p>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`glass-panel border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-200 ${
          isDragging 
            ? 'border-white bg-neutral-900' 
            : 'border-neutral-800 hover:border-neutral-600'
        }`}
      >
        <div className="w-16 h-16 rounded-xl bg-neutral-900 border border-neutral-800 flex items-center justify-center text-white mx-auto mb-4">
          <UploadCloud className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-white mb-1">
          {uploading ? "Analyzing & Profiling Dataset..." : "Drag and drop your dataset file here"}
        </h3>
        <p className="text-xs text-neutral-400 max-w-sm mx-auto mb-6">
          Supports .CSV and .XLSX datasets up to 50MB with automated columnar schema detection.
        </p>

        <label className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-white text-black font-bold text-sm cursor-pointer hover:bg-neutral-200 transition-colors">
          <span>Browse File</span>
          <input
            type="file"
            accept=".csv, .xlsx, .xls"
            onChange={(e) => e.target.files && handleFileUpload(e.target.files[0])}
            className="hidden"
            disabled={uploading}
          />
        </label>
      </div>



      {error && (
        <div className="p-4 rounded-lg bg-neutral-900 border border-neutral-700 text-neutral-200 text-sm flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-white" />
          <span>{error}</span>
        </div>
      )}

      {/* Profile Overview Card (If dataset is active) */}
      {selectedDataset && (
        <div className="glass-panel p-6 sm:p-8 rounded-xl border border-neutral-800 space-y-6 animate-fadeIn">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-neutral-800 gap-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-xl bg-neutral-900 border border-neutral-800 flex items-center justify-center text-white">
                <FileSpreadsheet className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">{selectedDataset.originalName}</h3>
                <p className="text-xs text-neutral-400 font-mono mt-0.5">
                  {(selectedDataset.fileSize / 1024).toFixed(1)} KB • Ingested Successfully
                </p>
              </div>
            </div>

            <button
              onClick={() => onProceedToWorkspace(selectedDataset)}
              className="px-5 py-2.5 rounded-lg bg-white text-black hover:bg-neutral-200 font-bold text-sm flex items-center justify-center space-x-2 transition-colors"
            >
              <span>Open Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg bg-black border border-neutral-800">
              <span className="text-xs text-neutral-400 font-mono uppercase">Rows</span>
              <div className="text-2xl font-extrabold text-white mt-1">{selectedDataset.rowCount}</div>
            </div>
            <div className="p-4 rounded-lg bg-black border border-neutral-800">
              <span className="text-xs text-neutral-400 font-mono uppercase">Columns</span>
              <div className="text-2xl font-extrabold text-white mt-1">{selectedDataset.colCount}</div>
            </div>
            <div className="p-4 rounded-lg bg-black border border-neutral-800">
              <span className="text-xs text-neutral-400 font-mono uppercase">Data Quality</span>
              <div className="text-2xl font-extrabold text-white mt-1">{selectedDataset.qualityScore}/100</div>
            </div>
            <div className="p-4 rounded-lg bg-black border border-neutral-800">
              <span className="text-xs text-neutral-400 font-mono uppercase">Numerical Features</span>
              <div className="text-2xl font-extrabold text-white mt-1">{selectedDataset.numericalColumns.length}</div>
            </div>
          </div>

          {/* Column Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
            <div className="p-4 rounded-lg bg-black border border-neutral-800 space-y-2">
              <div className="text-neutral-400 font-semibold uppercase tracking-wider flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-white" />
                <span>Numerical ({selectedDataset.numericalColumns.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {selectedDataset.numericalColumns.map((c, i) => (
                  <span key={i} className="px-2 py-1 rounded bg-neutral-900 text-neutral-200 border border-neutral-800">{c}</span>
                ))}
              </div>
            </div>

            <div className="p-4 rounded-lg bg-black border border-neutral-800 space-y-2">
              <div className="text-neutral-400 font-semibold uppercase tracking-wider flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-neutral-400" />
                <span>Categorical ({selectedDataset.categoricalColumns.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {selectedDataset.categoricalColumns.map((c, i) => (
                  <span key={i} className="px-2 py-1 rounded bg-neutral-900 text-neutral-200 border border-neutral-800">{c}</span>
                ))}
              </div>
            </div>

            <div className="p-4 rounded-lg bg-black border border-neutral-800 space-y-2">
              <div className="text-neutral-400 font-semibold uppercase tracking-wider flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-neutral-600" />
                <span>Date Columns ({selectedDataset.dateColumns.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {selectedDataset.dateColumns.length > 0 ? (
                  selectedDataset.dateColumns.map((c, i) => (
                    <span key={i} className="px-2 py-1 rounded bg-neutral-900 text-neutral-200 border border-neutral-800">{c}</span>
                  ))
                ) : (
                  <span className="text-neutral-500">None detected</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

