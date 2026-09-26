import mongoose, { Schema, Document } from 'mongoose';

export interface IAnalysisSession extends Document {
  datasetId: mongoose.Types.ObjectId;
  userQuestion: string;
  status: 'pending' | 'running' | 'approval_required' | 'completed' | 'failed';
  approvalPrompt?: string;
  isApproved: boolean;
  plan?: any;
  observations: any[];
  charts: any[];
  validationResult?: any;
  finalReport?: any;
  traceLogs: any[];
  createdAt: Date;
  updatedAt: Date;
}

const AnalysisSessionSchema: Schema = new Schema({
  datasetId: { type: Schema.Types.ObjectId, ref: 'Dataset', required: true },
  userQuestion: { type: String, required: true },
  status: { 
    type: String, 
    enum: ['pending', 'running', 'approval_required', 'completed', 'failed'],
    default: 'pending' 
  },
  approvalPrompt: { type: String },
  isApproved: { type: Boolean, default: false },
  plan: { type: Schema.Types.Mixed },
  observations: [{ type: Schema.Types.Mixed }],
  charts: [{ type: Schema.Types.Mixed }],
  validationResult: { type: Schema.Types.Mixed },
  finalReport: { type: Schema.Types.Mixed },
  traceLogs: [{ type: Schema.Types.Mixed }],
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now }
});

export default mongoose.model<IAnalysisSession>('AnalysisSession', AnalysisSessionSchema);
