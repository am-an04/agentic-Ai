import { Request, Response } from 'express';
import axios from 'axios';
import Dataset from '../models/Dataset';
import AnalysisSession from '../models/AnalysisSession';

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';

export const startAnalysis = async (req: Request, res: Response) => {
  try {
    const { datasetId, userQuestion, enableMl } = req.body;

    if (!datasetId || !userQuestion) {
      return res.status(400).json({ error: "'datasetId' and 'userQuestion' are required." });
    }

    const dataset = await Dataset.findById(datasetId);
    if (!dataset) {
      return res.status(404).json({ error: "Dataset not found." });
    }

    const session = new AnalysisSession({
      datasetId: dataset._id,
      userQuestion,
      status: 'running'
    });
    await session.save();

    // Call Python AI microservice
    try {
      const aiResponse = await axios.post(`${AI_SERVICE_URL}/api/analyze`, {
        dataset_path: dataset.filePath,
        user_question: userQuestion,
        session_id: session._id.toString(),
        enable_ml: enableMl ?? true
      });

      const data = aiResponse.data;
      session.status = data.completed ? 'completed' : (data.requires_human_approval ? 'approval_required' : 'running');
      session.approvalPrompt = data.approval_prompt;
      session.plan = data.plan;
      session.observations = data.observations || [];
      session.charts = data.charts || [];
      session.validationResult = data.validation_result;
      session.finalReport = data.final_report;
      session.traceLogs = data.trace_logs || [];
      session.sources = data.sources || [];
      session.updatedAt = new Date();

      await session.save();

      return res.json({
        sessionId: session._id,
        status: session.status,
        session
      });
    } catch (aiErr: any) {
      session.status = 'failed';
      session.traceLogs.push({ step: 'Error', description: aiErr.message, timestamp: Date.now() });
      await session.save();
      return res.status(500).json({ error: `AI microservice error: ${aiErr.message}`, session });
    }
  } catch (err: any) {
    return res.status(500).json({ error: err.message });
  }
};

export const approveAction = async (req: Request, res: Response) => {
  try {
    const { sessionId, approved } = req.body;

    const session = await AnalysisSession.findById(sessionId);
    if (!session) {
      return res.status(404).json({ error: "Analysis session not found." });
    }

    const aiResponse = await axios.post(`${AI_SERVICE_URL}/api/approve`, {
      session_id: session._id.toString(),
      approved: Boolean(approved)
    });

    const data = aiResponse.data;
    session.isApproved = Boolean(approved);
    session.status = data.completed ? 'completed' : 'running';
    session.observations = data.observations || session.observations;
    session.charts = data.charts || session.charts;
    session.validationResult = data.validation_result || session.validationResult;
    session.finalReport = data.final_report;
    session.traceLogs = data.trace_logs || session.traceLogs;
    session.sources = data.sources || session.sources;
    session.updatedAt = new Date();

    await session.save();

    return res.json({
      sessionId: session._id,
      status: session.status,
      session
    });
  } catch (err: any) {
    return res.status(500).json({ error: err.message });
  }
};

export const getSessionById = async (req: Request, res: Response) => {
  try {
    const session = await AnalysisSession.findById(req.params.id).populate('datasetId');
    if (!session) {
      return res.status(404).json({ error: "Session not found." });
    }
    return res.json(session);
  } catch (err: any) {
    return res.status(500).json({ error: err.message });
  }
};

export const listSessions = async (req: Request, res: Response) => {
  try {
    const sessions = await AnalysisSession.find().sort({ createdAt: -1 }).populate('datasetId');
    return res.json(sessions);
  } catch (err: any) {
    return res.status(500).json({ error: err.message });
  }
};

export const deleteSession = async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const session = await AnalysisSession.findByIdAndDelete(id);
    if (!session) {
      return res.status(404).json({ error: "Session not found." });
    }
    // Clean up microservice state if present
    try {
      await axios.delete(`${AI_SERVICE_URL}/api/session/${id}`).catch(() => {});
    } catch (_) {}
    return res.json({ message: "Analysis session deleted successfully.", id });
  } catch (err: any) {
    return res.status(500).json({ error: err.message });
  }
};

export const deleteAllSessions = async (_req: Request, res: Response) => {
  try {
    const result = await AnalysisSession.deleteMany({});
    // Clean up microservice states
    try {
      await axios.delete(`${AI_SERVICE_URL}/api/sessions`).catch(() => {});
    } catch (_) {}
    return res.json({ message: "All analyzed sessions deleted successfully.", deletedCount: result.deletedCount });
  } catch (err: any) {
    return res.status(500).json({ error: err.message });
  }
};

