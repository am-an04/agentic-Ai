import path from 'path';
import fs from 'fs';
import Dataset from '../models/Dataset';

export const seedDefaultDatasets = async (force: boolean = false) => {
  try {
    const count = await Dataset.countDocuments();
    if (count > 0 && !force) {
      console.log(`[Database] Found ${count} existing datasets. Skipping seed.`);
      return;
    }

    const uploadsDir = path.resolve(__dirname, '../../uploads');
    if (!fs.existsSync(uploadsDir)) {
      fs.mkdirSync(uploadsDir, { recursive: true });
    }

    const datasetsDir = path.resolve(__dirname, '../../../datasets');
    if (!fs.existsSync(datasetsDir)) {
      console.log('[Database Seed] Datasets directory not found, skipping seed.');
      return;
    }

    const sampleFiles = [
      {
        originalName: 'sales_churn_analytics.csv',
        filename: 'sales_churn_analytics.csv',
        rowCount: 31,
        colCount: 11,
        qualityScore: 98,
        columns: ['order_id','order_date','region','product_category','product_name','revenue','quantity','discount','customer_id','customer_segment','churn_risk'],
        numericalColumns: ['revenue','quantity','discount','churn_risk'],
        categoricalColumns: ['order_id','region','product_category','product_name','customer_id','customer_segment'],
        dateColumns: ['order_date']
      },
      {
        originalName: 'customer_segmentation.csv',
        filename: 'customer_segmentation.csv',
        rowCount: 15,
        colCount: 6,
        qualityScore: 95,
        columns: ['customer_id','recency_days','frequency_orders','monetary_value','preferred_category','satisfaction_score'],
        numericalColumns: ['recency_days','frequency_orders','monetary_value','satisfaction_score'],
        categoricalColumns: ['customer_id','preferred_category'],
        dateColumns: []
      }
    ];

    for (const item of sampleFiles) {
      const srcPath = path.join(datasetsDir, item.filename);
      if (fs.existsSync(srcPath)) {
        const destPath = path.join(uploadsDir, item.filename);
        fs.copyFileSync(srcPath, destPath);
        const stats = fs.statSync(destPath);

        const existing = await Dataset.findOne({ originalName: item.originalName });
        if (existing) {
          existing.filePath = destPath;
          existing.fileSize = stats.size;
          existing.rowCount = item.rowCount;
          existing.colCount = item.colCount;
          existing.qualityScore = item.qualityScore;
          await existing.save();
          console.log(`[Database Seed] Updated existing default dataset: ${item.originalName}`);
        } else {
          const dataset = new Dataset({
            filename: item.filename,
            originalName: item.originalName,
            filePath: destPath,
            fileSize: stats.size,
            mimeType: 'text/csv',
            rowCount: item.rowCount,
            colCount: item.colCount,
            qualityScore: item.qualityScore,
            columns: item.columns,
            numericalColumns: item.numericalColumns,
            categoricalColumns: item.categoricalColumns,
            dateColumns: item.dateColumns,
            profileSummary: {
              row_count: item.rowCount,
              col_count: item.colCount,
              columns: item.columns,
              numerical_columns: item.numericalColumns,
              categorical_columns: item.categoricalColumns,
              date_columns: item.dateColumns,
              data_quality_score: item.qualityScore
            }
          });
          await dataset.save();
          console.log(`[Database Seed] Seeded dataset: ${item.originalName}`);
        }
      }
    }
  } catch (err: any) {
    console.warn('[Database Seed] Seeding error:', err.message);
  }
};
