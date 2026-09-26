import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from app.tools.profiling_tools import load_dataset

def correlation_analysis(file_path: str, columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """Computes correlation matrix and identifies strongest linear relationships."""
    df = load_dataset(file_path)
    num_df = df.select_dtypes(include=[np.number])
    
    if columns:
        valid_cols = [c for c in columns if c in num_df.columns]
        if valid_cols:
            num_df = num_df[valid_cols]
            
    if num_df.empty or num_df.shape[1] < 2:
        return {"error": "Not enough numerical columns for correlation analysis."}
        
    corr_matrix = num_df.corr().round(4)
    
    # Identify strong correlations (exclude self-correlation)
    pairs = []
    cols = num_df.columns
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = float(corr_matrix.iloc[i, j])
            if not np.isnan(val):
                pairs.append({
                    "var1": cols[i],
                    "var2": cols[j],
                    "correlation": val,
                    "abs_correlation": abs(val)
                })
                
    pairs.sort(key=lambda x: x["abs_correlation"], reverse=True)
    top_correlations = pairs[:10]
    
    # Format correlation matrix for json
    matrix_dict = {col: corr_matrix[col].to_dict() for col in corr_matrix.columns}
    
    return {
        "correlation_matrix": matrix_dict,
        "top_correlations": top_correlations,
        "summary": f"Calculated correlations across {len(cols)} numerical variables. Top relationship: '{top_correlations[0]['var1']}' & '{top_correlations[0]['var2']}' (r = {top_correlations[0]['correlation']})." if top_correlations else "No correlations calculated."
    }

def group_by_analysis(file_path: str, group_col: str, target_col: str, agg_funcs: List[str] = ["mean", "sum", "count"]) -> Dict[str, Any]:
    """Performs group-by aggregation of a target metric across categorical groups."""
    df = load_dataset(file_path)
    
    if group_col not in df.columns:
        return {"error": f"Group column '{group_col}' not found in dataset."}
    if target_col not in df.columns:
        return {"error": f"Target column '{target_col}' not found in dataset."}
        
    grouped = df.groupby(group_col)[target_col].agg(agg_funcs).reset_index()
    
    # Sort by the first agg func (usually sum or mean) descending
    sort_col = agg_funcs[0]
    grouped = grouped.sort_values(by=sort_col, ascending=False)
    
    records = grouped.to_dict(orient="records")
    
    total_val = float(df[target_col].sum()) if pd.api.types.is_numeric_dtype(df[target_col]) else 0
    
    # Add percentage of total if sum is calculated
    if "sum" in agg_funcs and total_val > 0:
        for r in records:
            r["percentage_of_total"] = round((float(r["sum"]) / total_val) * 100, 2)

    top_group = records[0][group_col] if records else "N/A"
    top_val = records[0].get(sort_col, "N/A") if records else "N/A"

    return {
        "group_col": group_col,
        "target_col": target_col,
        "group_results": records,
        "summary": f"Grouped by '{group_col}' on '{target_col}'. Top group: '{top_group}' with {sort_col} = {top_val}."
    }

def trend_analysis(file_path: str, date_col: str, value_col: str, freq: str = "Q") -> Dict[str, Any]:
    """Analyzes time-series trends and period-over-period percentage changes (Monthly 'M' or Quarterly 'Q')."""
    df = load_dataset(file_path)
    
    if date_col not in df.columns:
        return {"error": f"Date column '{date_col}' not found in dataset."}
    if value_col not in df.columns:
        return {"error": f"Value column '{value_col}' not found in dataset."}
        
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    valid_df = df.dropna(subset=[date_col]).sort_values(by=date_col)
    
    if valid_df.empty:
        return {"error": f"No valid date entries found in '{date_col}'."}
        
    resampled = valid_df.set_index(date_col).resample(freq)[value_col].agg(["sum", "mean", "count"]).reset_index()
    
    # Format date string labels (e.g. '2025-Q1', '2025-Q2', '2025-Q3')
    if freq == "Q":
        resampled["period_label"] = resampled[date_col].dt.to_period("Q").astype(str)
    elif freq == "M":
        resampled["period_label"] = resampled[date_col].dt.to_period("M").astype(str)
    else:
        resampled["period_label"] = resampled[date_col].astype(str)
        
    resampled["pct_change"] = resampled["sum"].pct_change() * 100
    resampled["pct_change"] = resampled["pct_change"].round(2).fillna(0.0)
    
    records = []
    for _, row in resampled.iterrows():
        records.append({
            "period": str(row["period_label"]),
            "total_value": float(round(row["sum"], 2)),
            "average_value": float(round(row["mean"], 2)),
            "count": int(row["count"]),
            "pct_change_vs_prior": float(row["pct_change"])
        })
        
    # Detect major drops or spikes
    significant_changes = [r for r in records if abs(r["pct_change_vs_prior"]) >= 10.0]

    return {
        "date_col": date_col,
        "value_col": value_col,
        "freq": freq,
        "trend_data": records,
        "significant_changes": significant_changes,
        "summary": f"Analyzed trend for '{value_col}' over '{date_col}' grouped by '{freq}'. Generated {len(records)} periods."
    }

def distribution_analysis(file_path: str, column: str) -> Dict[str, Any]:
    """Calculates detailed distribution statistics for a specific column."""
    df = load_dataset(file_path)
    
    if column not in df.columns:
        return {"error": f"Column '{column}' not found in dataset."}
        
    series = df[column].dropna()
    
    if pd.api.types.is_numeric_dtype(series):
        stats = {
            "mean": float(series.mean()),
            "std": float(series.std()),
            "median": float(series.median()),
            "skewness": float(series.skew()),
            "kurtosis": float(series.kurtosis()),
            "min": float(series.min()),
            "max": float(series.max()),
            "q25": float(series.quantile(0.25)),
            "q75": float(series.quantile(0.75)),
            "iqr": float(series.quantile(0.75) - series.quantile(0.25))
        }
        # Histogram bins
        counts, bin_edges = np.histogram(series, bins=10)
        bins = []
        for i in range(len(counts)):
            bins.append({
                "bin_start": float(round(bin_edges[i], 2)),
                "bin_end": float(round(bin_edges[i+1], 2)),
                "count": int(counts[i])
            })
        return {
            "column": column,
            "type": "numerical",
            "statistics": stats,
            "histogram": bins,
            "summary": f"Numerical distribution of '{column}': mean = {stats['mean']:.2f}, median = {stats['median']:.2f}, skewness = {stats['skewness']:.2f}."
        }
    else:
        vc = series.value_counts().head(10).to_dict()
        formatted_vc = [{str(k): int(v)} for k, v in vc.items()]
        return {
            "column": column,
            "type": "categorical",
            "top_values": formatted_vc,
            "unique_count": int(series.nunique()),
            "summary": f"Categorical distribution of '{column}': {series.nunique()} unique values. Most frequent: '{series.mode().iloc[0]}'."
        }
