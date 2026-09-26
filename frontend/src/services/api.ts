import axios from 'axios';
import { Dataset, AnalysisSession, AnalysisReport } from '../types';

const API_BASE = '/api';

export const api = {
  // Datasets
  async uploadDataset(file: File): Promise<{ message: string; dataset: Dataset }> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await axios.post(`${API_BASE}/datasets/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },

  async listDatasets(): Promise<Dataset[]> {
    const res = await axios.get(`${API_BASE}/datasets`);
    return res.data;
  },

  async getDataset(id: string): Promise<Dataset> {
    const res = await axios.get(`${API_BASE}/datasets/${id}`);
    return res.data;
  },

  async deleteDataset(id: string): Promise<{ message: string; id: string }> {
    const res = await axios.delete(`${API_BASE}/datasets/${id}`);
    return res.data;
  },

  // Analysis Sessions
  async startAnalysis(datasetId: string, userQuestion: string, enableMl: boolean = true): Promise<{ sessionId: string; status: string; session: AnalysisSession }> {
    const res = await axios.post(`${API_BASE}/analysis/start`, {
      datasetId,
      userQuestion,
      enableMl
    });
    return res.data;
  },

  async approveAction(sessionId: string, approved: boolean): Promise<{ sessionId: string; status: string; session: AnalysisSession }> {
    const res = await axios.post(`${API_BASE}/analysis/approve`, {
      sessionId,
      approved
    });
    return res.data;
  },

  async getSession(id: string): Promise<AnalysisSession> {
    const res = await axios.get(`${API_BASE}/analysis/session/${id}`);
    return res.data;
  },

  async listSessions(): Promise<AnalysisSession[]> {
    const res = await axios.get(`${API_BASE}/analysis/sessions`);
    return res.data;
  },

  async deleteSession(id: string): Promise<{ message: string; id: string }> {
    const res = await axios.delete(`${API_BASE}/analysis/session/${id}`);
    return res.data;
  },

  async deleteAllSessions(): Promise<{ message: string; deletedCount: number }> {
    const res = await axios.delete(`${API_BASE}/analysis/sessions`);
    return res.data;
  }
};
