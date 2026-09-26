"""
RAG / Knowledge Layer for DataPilot AI Data Analyst
Contains analytical guidelines, statistical rules, ML best practices, and visualization selection logic.
"""

ANALYTICAL_KNOWLEDGE_BASE = {
    "statistical_guidelines": {
        "p_value_threshold": 0.05,
        "sample_size_minimum": 30,
        "ttest_rule": "Use independent 2-sample t-test when comparing continuous metric across 2 categorical groups.",
        "anova_rule": "Use 1-way ANOVA when comparing continuous metric across 3+ categorical groups.",
        "chi_square_rule": "Use Chi-Square test when evaluating association between 2 categorical variables.",
        "correlation_vs_causation": "Always state linear association rather than causal direction unless controlled experiment design is confirmed."
    },
    "ml_guidelines": {
        "regression_metrics": ["MAE", "RMSE", "R2_score"],
        "classification_metrics": ["Accuracy", "Precision", "Recall", "F1_score", "Confusion Matrix"],
        "clustering_metrics": ["Silhouette Score"],
        "overfitting_rule": "Always evaluate models on a 20% holdout test set with random state reproducibility."
    },
    "visualization_guidelines": {
        "trend": "Use Line Chart for continuous time series (dates/quarters).",
        "category_comparison": "Use Bar Chart for comparing aggregated values across categories.",
        "relationship": "Use Scatter Plot for bivariate continuous variable relationships.",
        "distribution": "Use Box Plot or Histogram for spread, quartiles, and outliers."
    },
    "reporting_guidelines": {
        "transparency": "Every finding must be supported by an empirical tool observation.",
        "actionability": "Recommendations must directly reference findings and statistical metrics."
    }
}

def get_methodology_guidance(topic: str) -> str:
    """Retrieves relevant analytical guidelines based on the topic."""
    if topic in ANALYTICAL_KNOWLEDGE_BASE:
        return str(ANALYTICAL_KNOWLEDGE_BASE[topic])
    return str(ANALYTICAL_KNOWLEDGE_BASE)
