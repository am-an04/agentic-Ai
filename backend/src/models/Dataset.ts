import mongoose, { Schema, Document } from 'mongoose';

export interface IDataset extends Document {
  filename: string;
  originalName: string;
  filePath: string;
  fileSize: number;
  mimeType: string;
  rowCount: number;
  colCount: number;
  qualityScore: number;
  columns: string[];
  numericalColumns: string[];
  categoricalColumns: string[];
  dateColumns: string[];
  profileSummary?: any;
  createdAt: Date;
}

const DatasetSchema: Schema = new Schema({
  filename: { type: String, required: true },
  originalName: { type: String, required: true },
  filePath: { type: String, required: true },
  fileSize: { type: Number, required: true },
  mimeType: { type: String, required: true },
  rowCount: { type: Number, default: 0 },
  colCount: { type: Number, default: 0 },
  qualityScore: { type: Number, default: 100 },
  columns: [{ type: String }],
  numericalColumns: [{ type: String }],
  categoricalColumns: [{ type: String }],
  dateColumns: [{ type: String }],
  profileSummary: { type: Schema.Types.Mixed },
  createdAt: { type: Date, default: Date.now }
});

export default mongoose.model<IDataset>('Dataset', DatasetSchema);
