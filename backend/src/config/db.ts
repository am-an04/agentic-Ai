import mongoose from 'mongoose';

export const connectDB = async () => {
  try {
    const connStr = process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/datapilot';
    await mongoose.connect(connStr);
    console.log(`[Database] MongoDB connected: ${connStr}`);
  } catch (err: any) {
    console.warn(`[Database] MongoDB connection warning: ${err.message}. (Backend will continue running)`);
  }
};
