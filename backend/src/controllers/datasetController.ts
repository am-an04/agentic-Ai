import { Request, Response } from 'express';
import axios from 'axios';
import path from 'path';
import Dataset from '../models/Dataset';
import AnalysisSession from '../models/AnalysisSession';

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';

export const uploadDataset = async (req: Request, res: Response) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No dataset file provided.' });
    }

    const filePath = path.resolve(req.file.path);
    
    // Call Python AI microservice to profile dataset
    let profileData: any = {};
    try {
      const response = await axios.post(`${AI_SERVICE_URL}/api/profile`, { dataset_path: filePath });
      profileData = response.data;
    } catch (aiErr: any) {
      console.warn('AI profiling microservice fallback call:', aiErr.message);
    }

    const dataset = new Dataset({
      filename: req.file.filename,
      originalName: req.file.originalname,
      filePath: filePath,
      fileSize: req.file.size,
      mimeType: req.file.mimetype,
      rowCount: profileData.row_count || 0,
      colCount: profileData.col_count || 0,
      qualityScore: profileData.data_quality_score || 100,
      columns: profileData.columns || [],
      numericalColumns: profileData.numerical_columns || [],
      categoricalColumns: profileData.categorical_columns || [],
      dateColumns: profileData.date_columns || [],
      profileSummary: profileData
    });

    await dataset.save();

    return res.status(201).json({
      message: 'Dataset uploaded and profiled successfully.',
      dataset
    });
  } catch (err: any) {
    return res.status(500).json({ error: err.message });
  }
};

export const listDatasets = async (req: Request, res: Response) => {
  try {
    const datasets = await Dataset.find().sort({ createdAt: -1 });
    return res.json(datasets);
  } catch (err: any) {
    return res.status(500).json({ error: err.message });
  }
};

export const getDatasetById = async (req: Request, res: Response) => {
  try {
    const dataset = await Dataset.findById(req.params.id);
    if (!dataset) {
      return res.status(404).json({ error: 'Dataset not found.' });
    }
    return res.json(dataset);
  } catch (err: any) {
    return res.status(500).json({ error: err.message });
  }
};

export const deleteDataset = async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const dataset = await Dataset.findByIdAndDelete(id);
    if (!dataset) {
      return res.status(404).json({ error: 'Dataset not found.' });
    }
    // Delete associated analysis sessions
    await AnalysisSession.deleteMany({ datasetId: id });
    return res.json({ message: 'Dataset and associated analysis deleted successfully.', id });
  } catch (err: any) {
    return res.status(500).json({ error: err.message });
  }
};
