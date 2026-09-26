import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';
import { connectDB } from './config/db';
import datasetRoutes from './routes/datasetRoutes';
import analysisRoutes from './routes/analysisRoutes';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());
app.use('/uploads', express.static(path.resolve(__dirname, '../uploads')));

// Mount API routes
app.use('/api/datasets', datasetRoutes);
app.use('/api/analysis', analysisRoutes);

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'DataPilot Node Backend API Gateway' });
});

connectDB().then(() => {
  app.listen(PORT, () => {
    console.log(`[Backend API Gateway] Server running on http://localhost:${PORT}`);
  });
});
