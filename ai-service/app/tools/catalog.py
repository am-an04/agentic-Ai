"""
Tool Catalog for DataPilot Agentic AI System.
Contains real tools, descriptions, parameter schemas, and category tags.
"""

from typing import Dict, Any

TOOL_CATALOG: Dict[str, Dict[str, Any]] = {
    "profile_dataset": {
        "name": "profile_dataset",
        "category": "profiling",
        "description": "Inspects dataset shape, data types, missing counts, duplicate rows, outlier counts, and summary statistics.",
        "parameters": {},
        "requires_approval": False
    },
    "correlation_analysis": {
        "name": "correlation_analysis",
        "category": "eda",
        "description": "Computes Pearson correlation matrix and identifies top linear bivariate relationships among numerical columns.",
        "parameters": {
            "columns": {
                "type": "list[str]",
                "description": "Optional subset of numerical column names. If omitted, uses all numerical columns.",
                "required": False
            }
        },
        "requires_approval": False
    },
    "group_by_analysis": {
        "name": "group_by_analysis",
        "category": "eda",
        "description": "Aggregates a target numerical metric across categorical groups (e.g. mean, sum, count) and calculates contribution percentages.",
        "parameters": {
            "group_col": {
                "type": "str",
                "description": "Categorical column to group by.",
                "required": True
            },
            "target_col": {
                "type": "str",
                "description": "Numerical target column to aggregate.",
                "required": True
            },
            "agg_funcs": {
                "type": "list[str]",
                "description": "Aggregation functions such as ['mean', 'sum', 'count'].",
                "required": False,
                "default": ["mean", "sum", "count"]
            }
        },
        "requires_approval": False
    },
    "trend_analysis": {
        "name": "trend_analysis",
        "category": "eda",
        "description": "Calculates time-series trends and period-over-period percentage changes over a date column (freq 'Q' for quarterly or 'M' for monthly).",
        "parameters": {
            "date_col": {
                "type": "str",
                "description": "Date or datetime column name.",
                "required": True
            },
            "value_col": {
                "type": "str",
                "description": "Numerical metric column to track over time.",
                "required": True
            },
            "freq": {
                "type": "str",
                "description": "Resampling frequency ('Q' for quarterly, 'M' for monthly). Default is 'Q'.",
                "required": False,
                "default": "Q"
            }
        },
        "requires_approval": False
    },
    "distribution_analysis": {
        "name": "distribution_analysis",
        "category": "eda",
        "description": "Calculates detailed distribution statistics (mean, median, skewness, kurtosis, IQR) or frequency counts for a specific column.",
        "parameters": {
            "column": {
                "type": "str",
                "description": "Column name to analyze.",
                "required": True
            }
        },
        "requires_approval": False
    },
    "ttest": {
        "name": "ttest",
        "category": "stats",
        "description": "Independent two-sample Welch's t-test comparing a continuous metric across two distinct categories.",
        "parameters": {
            "group_col": {
                "type": "str",
                "description": "Categorical column with exactly 2 unique groups.",
                "required": True
            },
            "value_col": {
                "type": "str",
                "description": "Continuous numerical metric to compare across the groups.",
                "required": True
            }
        },
        "requires_approval": False
    },
    "chi_square": {
        "name": "chi_square",
        "category": "stats",
        "description": "Chi-Square test of independence and Cramér's V effect size between two categorical columns.",
        "parameters": {
            "col1": {
                "type": "str",
                "description": "First categorical column.",
                "required": True
            },
            "col2": {
                "type": "str",
                "description": "Second categorical column.",
                "required": True
            }
        },
        "requires_approval": False
    },
    "anova": {
        "name": "anova",
        "category": "stats",
        "description": "One-Way ANOVA test evaluating if a continuous metric varies significantly across 3 or more categorical groups.",
        "parameters": {
            "group_col": {
                "type": "str",
                "description": "Categorical grouping column with 2 or more categories.",
                "required": True
            },
            "value_col": {
                "type": "str",
                "description": "Continuous numerical value column.",
                "required": True
            }
        },
        "requires_approval": False
    },
    "train_regression": {
        "name": "train_regression",
        "category": "ml",
        "description": "Trains a machine learning regression model (RandomForest, Linear, or GradientBoosting) to predict a continuous numerical column.",
        "parameters": {
            "target_col": {
                "type": "str",
                "description": "Continuous numerical target column.",
                "required": True
            },
            "feature_cols": {
                "type": "list[str]",
                "description": "Predictor feature column names.",
                "required": False
            },
            "model_type": {
                "type": "str",
                "description": "'random_forest' | 'linear' | 'gradient_boosting'. Default is 'random_forest'.",
                "required": False,
                "default": "random_forest"
            }
        },
        "requires_approval": True
    },
    "train_classification": {
        "name": "train_classification",
        "category": "ml",
        "description": "Trains a machine learning classification model (RandomForest, Logistic, or GradientBoosting) to predict a discrete target column.",
        "parameters": {
            "target_col": {
                "type": "str",
                "description": "Discrete target variable column.",
                "required": True
            },
            "feature_cols": {
                "type": "list[str]",
                "description": "Predictor feature column names.",
                "required": False
            },
            "model_type": {
                "type": "str",
                "description": "'random_forest' | 'logistic' | 'gradient_boosting'. Default is 'random_forest'.",
                "required": False,
                "default": "random_forest"
            }
        },
        "requires_approval": True
    },
    "train_clustering": {
        "name": "train_clustering",
        "category": "ml",
        "description": "Segments dataset records into clusters using K-Means clustering across numerical features.",
        "parameters": {
            "feature_cols": {
                "type": "list[str]",
                "description": "Numerical feature columns for clustering.",
                "required": False
            },
            "n_clusters": {
                "type": "int",
                "description": "Number of clusters to create. Default is 3.",
                "required": False,
                "default": 3
            }
        },
        "requires_approval": True
    },
    "bar_chart": {
        "name": "bar_chart",
        "category": "viz",
        "description": "Generates an interactive Plotly bar chart comparing a metric across categorical groups.",
        "parameters": {
            "x_col": {
                "type": "str",
                "description": "Categorical column for x-axis.",
                "required": True
            },
            "y_col": {
                "type": "str",
                "description": "Numerical column for y-axis.",
                "required": True
            },
            "color_col": {
                "type": "str",
                "description": "Optional secondary categorical column for group coloring.",
                "required": False
            },
            "title": {
                "type": "str",
                "description": "Chart title.",
                "required": False
            }
        },
        "requires_approval": False
    },
    "line_chart": {
        "name": "line_chart",
        "category": "viz",
        "description": "Generates an interactive Plotly line chart for time-series or trend visualization.",
        "parameters": {
            "x_col": {
                "type": "str",
                "description": "Date or chronological column for x-axis.",
                "required": True
            },
            "y_col": {
                "type": "str",
                "description": "Numerical column for y-axis.",
                "required": True
            },
            "color_col": {
                "type": "str",
                "description": "Optional categorical column to separate multiple lines.",
                "required": False
            },
            "title": {
                "type": "str",
                "description": "Chart title.",
                "required": False
            }
        },
        "requires_approval": False
    },
    "scatter_plot": {
        "name": "scatter_plot",
        "category": "viz",
        "description": "Generates an interactive Plotly scatter plot with OLS trendline to examine the relationship between two numerical variables.",
        "parameters": {
            "x_col": {
                "type": "str",
                "description": "Numerical column for x-axis.",
                "required": True
            },
            "y_col": {
                "type": "str",
                "description": "Numerical column for y-axis.",
                "required": True
            },
            "color_col": {
                "type": "str",
                "description": "Optional categorical column for color hue.",
                "required": False
            },
            "title": {
                "type": "str",
                "description": "Chart title.",
                "required": False
            }
        },
        "requires_approval": False
    },
    "box_plot": {
        "name": "box_plot",
        "category": "viz",
        "description": "Generates an interactive Plotly box plot to inspect distributions, medians, and outliers across categories.",
        "parameters": {
            "category_col": {
                "type": "str",
                "description": "Categorical column for x-axis.",
                "required": True
            },
            "value_col": {
                "type": "str",
                "description": "Numerical column for y-axis.",
                "required": True
            },
            "title": {
                "type": "str",
                "description": "Chart title.",
                "required": False
            }
        },
        "requires_approval": False
    },
    "heatmap": {
        "name": "heatmap",
        "category": "viz",
        "description": "Generates an interactive Plotly correlation matrix heatmap for numerical columns.",
        "parameters": {
            "title": {
                "type": "str",
                "description": "Heatmap title.",
                "required": False
            }
        },
        "requires_approval": False
    },
    "validate_claims": {
        "name": "validate_claims",
        "category": "validation",
        "description": "Performs statistical validation audit, correlation-vs-causation check, and empirical claim verification.",
        "parameters": {},
        "requires_approval": False
    },
    "generate_report": {
        "name": "generate_report",
        "category": "report",
        "description": "Synthesizes final structured executive report with key findings, visual insights, and actionable recommendations.",
        "parameters": {},
        "requires_approval": False
    },
    "analyst_code": {
        "name": "analyst_code",
        "category": "sandbox",
        "description": "Executes safe, custom Pandas/NumPy calculation code in an isolated Python subprocess sandbox to compute specific metrics or transformations.",
        "parameters": {
            "code": {
                "type": "str",
                "description": "Python snippet that reads DataFrame 'df' and assigns final output to variable 'result'.",
                "required": True
            },
            "purpose": {
                "type": "str",
                "description": "Description of the calculation or transformation being performed.",
                "required": False
            }
        },
        "requires_approval": False
    }
}

TOOL_ALIASES: Dict[str, str] = {
    "linear_regression": "train_regression",
    "regression": "train_regression",
    "logistic_regression": "train_classification",
    "classification": "train_classification",
    "random_forest": "train_classification",
    "clustering": "train_clustering",
    "kmeans": "train_clustering",
    "k_means": "train_clustering",
    "two_sample_ttest": "ttest",
    "t_test": "ttest",
    "chi_square_test": "chi_square",
    "chisquare": "chi_square",
    "anova_test": "anova",
    "correlation": "correlation_analysis",
    "corr": "correlation_analysis",
    "barchart": "bar_chart",
    "linechart": "line_chart",
    "scatterplot": "scatter_plot",
    "boxplot": "box_plot",
    "distribution": "distribution_analysis",
    "python_sandbox": "analyst_code",
    "execute_code": "analyst_code",
    "python_code": "analyst_code",
    "run_code": "analyst_code",
    "custom_code": "analyst_code"
}

def resolve_tool_name(tool_name: str) -> str:
    """Resolves tool aliases to canonical tool names in TOOL_CATALOG."""
    canon = tool_name.strip().lower()
    if canon in TOOL_CATALOG:
        return canon
    return TOOL_ALIASES.get(canon, canon)
