import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List

def load_dataset(file_path: str) -> pd.DataFrame:
    """Loads a CSV or Excel dataset safely into a Pandas DataFrame."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found at: {file_path}")
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.csv':
        df = pd.read_csv(file_path)
    elif ext in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format '{ext}'. Supported formats are CSV and XLSX.")
    
    return df

def profile_dataset(file_path: str) -> Dict[str, Any]:
    """Inspects dataset and generates a comprehensive data profiling report."""
    df = load_dataset(file_path)
    
    row_count, col_count = df.shape
    duplicate_rows = int(df.duplicated().sum())
    
    dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
    missing_counts = df.isnull().sum().to_dict()
    missing_percentages = {col: round((count / row_count) * 100, 2) if row_count > 0 else 0.0 for col, count in missing_counts.items()}
    
    numerical_cols = []
    categorical_cols = []
    date_cols = []
    
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            numerical_cols.append(col)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
        else:
            # Try parsing as datetime if string
            try:
                sample = df[col].dropna().head(10)
                if len(sample) > 0 and pd.to_datetime(sample, format='mixed', errors='coerce').notnull().all():
                    date_cols.append(col)
                    continue
            except Exception:
                pass
            categorical_cols.append(col)

    # Detect potential targets
    potential_targets = []
    target_keywords = ['target', 'label', 'churn', 'sales', 'revenue', 'price', 'outcome', 'status', 'is_']
    for col in df.columns:
        if any(kw in col.lower() for kw in target_keywords):
            potential_targets.append(col)

    # Outlier detection using IQR
    outlier_counts = {}
    for col in numerical_cols:
        series = df[col].dropna()
        if len(series) > 0:
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = series[(series < lower_bound) | (series > upper_bound)]
            outlier_counts[col] = int(len(outliers))
        else:
            outlier_counts[col] = 0

    # Data Quality Issues
    quality_issues = []
    total_missing_pct = sum(missing_percentages.values()) / (col_count if col_count > 0 else 1)
    
    if duplicate_rows > 0:
        quality_issues.append(f"Found {duplicate_rows} duplicate rows ({round((duplicate_rows/row_count)*100, 1)}% of dataset).")
    
    for col, pct in missing_percentages.items():
        if pct > 0:
            quality_issues.append(f"Column '{col}' has {pct}% missing values.")
            
    for col in categorical_cols:
        unique_cnt = df[col].nunique()
        if unique_cnt == 1:
            quality_issues.append(f"Column '{col}' has a single constant value.")
        elif unique_cnt > 0.9 * row_count and row_count > 50:
            quality_issues.append(f"Column '{col}' has very high cardinality ({unique_cnt} unique values).")

    # Data Quality Score calculation
    penalty = (duplicate_rows / (row_count if row_count > 0 else 1)) * 20 + total_missing_pct * 0.5 + len(quality_issues) * 2
    quality_score = max(0.0, min(100.0, round(100.0 - penalty, 1)))

    # Basic stats
    summary_stats = {}
    if numerical_cols:
        desc = df[numerical_cols].describe().to_dict()
        # Format describe dict for JSON readiness
        for col, metrics in desc.items():
            summary_stats[col] = {k: float(v) if not np.isnan(v) else None for k, v in metrics.items()}
            
    for col in categorical_cols[:5]:  # Top 5 categorical cols
        vc = df[col].value_counts().head(5).to_dict()
        summary_stats[col] = {str(k): int(v) for k, v in vc.items()}

    return {
        "dataset_name": os.path.basename(file_path),
        "row_count": row_count,
        "col_count": col_count,
        "columns": list(df.columns),
        "dtypes": dtypes,
        "missing_counts": missing_counts,
        "missing_percentages": missing_percentages,
        "duplicate_rows": duplicate_rows,
        "numerical_columns": numerical_cols,
        "categorical_columns": categorical_cols,
        "date_columns": date_cols,
        "potential_targets": potential_targets,
        "outlier_counts": outlier_counts,
        "data_quality_score": quality_score,
        "data_quality_issues": quality_issues,
        "summary_stats": summary_stats
    }
