import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, List, Optional
from app.tools.profiling_tools import load_dataset

def two_sample_ttest(file_path: str, group_col: str, value_col: str) -> Dict[str, Any]:
    """Performs an independent two-sample t-test comparing value_col across two distinct categories in group_col."""
    df = load_dataset(file_path)
    
    if group_col not in df.columns or value_col not in df.columns:
        return {"error": f"Columns '{group_col}' or '{value_col}' not found."}
        
    valid_df = df.dropna(subset=[group_col, value_col])
    groups = valid_df[group_col].unique()
    
    if len(groups) != 2:
        return {"error": f"T-test requires exactly 2 unique groups in '{group_col}', but found {len(groups)}: {list(groups)[:5]}."}
        
    g1_data = valid_df[valid_df[group_col] == groups[0]][value_col]
    g2_data = valid_df[valid_df[group_col] == groups[1]][value_col]
    
    if len(g1_data) < 3 or len(g2_data) < 3:
        return {"error": "Insufficient sample size in one or both groups for a reliable t-test (n < 3)."}
        
    t_stat, p_val = stats.ttest_ind(g1_data, g2_data, equal_var=False)
    
    m1, m2 = float(g1_data.mean()), float(g2_data.mean())
    diff = m1 - m2
    
    # 95% Confidence Interval for mean difference
    se = np.sqrt(g1_data.var()/len(g1_data) + g2_data.var()/len(g2_data))
    ci_lower = diff - 1.96 * se
    ci_upper = diff + 1.96 * se
    
    is_significant = float(p_val) < 0.05
    
    explanation = (
        f"Compared mean '{value_col}' between '{groups[0]}' (mean={m1:.2f}, n={len(g1_data)}) and "
        f"'{groups[1]}' (mean={m2:.2f}, n={len(g2_data)}). "
        f"Difference: {diff:.2f} (95% CI: [{ci_lower:.2f}, {ci_upper:.2f}]). "
        f"t-statistic = {t_stat:.3f}, p-value = {p_val:.4f}. "
        f"Result is {'statistically SIGNIFICANT (p < 0.05)' if is_significant else 'NOT statistically significant (p >= 0.05)'}."
    )

    return {
        "test_type": "Two-sample t-test (Welch's)",
        "group_col": group_col,
        "value_col": value_col,
        "group1": str(groups[0]),
        "group1_mean": m1,
        "group1_n": len(g1_data),
        "group2": str(groups[1]),
        "group2_mean": m2,
        "group2_n": len(g2_data),
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "mean_difference": float(diff),
        "ci_95": [float(ci_lower), float(ci_upper)],
        "is_significant": is_significant,
        "summary": explanation
    }

def chi_square_test(file_path: str, col1: str, col2: str) -> Dict[str, Any]:
    """Performs a Chi-Square test of independence between two categorical variables."""
    df = load_dataset(file_path)
    
    if col1 not in df.columns or col2 not in df.columns:
        return {"error": f"Columns '{col1}' or '{col2}' not found."}
        
    contingency_table = pd.crosstab(df[col1], df[col2])
    
    if contingency_table.empty or contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
        return {"error": "Contingency table must be at least 2x2."}
        
    chi2, p_val, dof, expected = stats.chi2_contingency(contingency_table)
    
    # Calculate Cramér's V for effect size
    n = contingency_table.sum().sum()
    min_dim = min(contingency_table.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 and n > 0 else 0.0
    
    is_significant = float(p_val) < 0.05
    
    explanation = (
        f"Chi-square test of independence between '{col1}' and '{col2}'. "
        f"chi2 = {chi2:.3f}, dof = {dof}, p-value = {p_val:.4f}, Cramér's V = {cramers_v:.3f}. "
        f"The association is {'statistically SIGNIFICANT (p < 0.05)' if is_significant else 'NOT statistically significant (p >= 0.05)'}."
    )

    return {
        "test_type": "Chi-Square Test of Independence",
        "col1": col1,
        "col2": col2,
        "chi2_statistic": float(chi2),
        "p_value": float(p_val),
        "degrees_of_freedom": int(dof),
        "cramers_v": float(cramers_v),
        "is_significant": is_significant,
        "summary": explanation
    }

def anova_test(file_path: str, group_col: str, value_col: str) -> Dict[str, Any]:
    """Performs a One-Way ANOVA across 3 or more groups."""
    df = load_dataset(file_path)
    
    if group_col not in df.columns or value_col not in df.columns:
        return {"error": f"Columns '{group_col}' or '{value_col}' not found."}
        
    valid_df = df.dropna(subset=[group_col, value_col])
    groups = valid_df[group_col].unique()
    
    if len(groups) < 2:
        return {"error": f"ANOVA requires at least 2 groups in '{group_col}', found {len(groups)}."}
        
    group_data = [valid_df[valid_df[group_col] == g][value_col] for g in groups]
    
    f_stat, p_val = stats.f_oneway(*group_data)
    
    group_means = {str(g): float(valid_df[valid_df[group_col] == g][value_col].mean()) for g in groups}
    
    is_significant = float(p_val) < 0.05
    
    explanation = (
        f"One-way ANOVA for '{value_col}' grouped by '{group_col}' across {len(groups)} groups. "
        f"F-statistic = {f_stat:.3f}, p-value = {p_val:.4f}. "
        f"Group differences are {'statistically SIGNIFICANT (p < 0.05)' if is_significant else 'NOT statistically significant (p >= 0.05)'}."
    )

    return {
        "test_type": "One-Way ANOVA",
        "group_col": group_col,
        "value_col": value_col,
        "f_statistic": float(f_stat),
        "p_value": float(p_val),
        "group_means": group_means,
        "is_significant": is_significant,
        "summary": explanation
    }
