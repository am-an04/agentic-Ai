import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
from typing import Dict, Any, List, Optional
from app.tools.profiling_tools import load_dataset

# Ensure plotly outputs clean json dicts
pio.templates.default = "plotly_dark"

import json

def _serialize_plotly(fig) -> Dict[str, Any]:
    """Converts a Plotly figure to a JSON-serializable dict representation."""
    return json.loads(fig.to_json())

def create_bar_chart(file_path: str, x_col: str, y_col: str, color_col: Optional[str] = None, title: str = "") -> Dict[str, Any]:
    """Generates an interactive Plotly bar chart."""
    df = load_dataset(file_path)
    
    if x_col not in df.columns or y_col not in df.columns:
        return {"error": f"Columns '{x_col}' or '{y_col}' not found."}
        
    agg_df = df.groupby(x_col)[y_col].mean().reset_index()
    if color_col and color_col in df.columns:
        agg_df = df.groupby([x_col, color_col])[y_col].mean().reset_index()
        fig = px.bar(agg_df, x=x_col, y=y_col, color=color_col, title=title or f"Average {y_col} by {x_col}", barmode="group")
    else:
        fig = px.bar(agg_df, x=x_col, y=y_col, title=title or f"Average {y_col} by {x_col}")
        
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    
    return {
        "chart_type": "bar",
        "title": title or f"Average {y_col} by {x_col}",
        "x_col": x_col,
        "y_col": y_col,
        "chart_spec": _serialize_plotly(fig),
        "summary": f"Generated bar chart for {y_col} grouped by {x_col}."
    }

def create_line_chart(file_path: str, x_col: str, y_col: str, color_col: Optional[str] = None, title: str = "") -> Dict[str, Any]:
    """Generates an interactive Plotly line chart (ideal for time series and trends)."""
    df = load_dataset(file_path)
    
    if x_col not in df.columns or y_col not in df.columns:
        return {"error": f"Columns '{x_col}' or '{y_col}' not found."}
        
    df[x_col] = pd.to_datetime(df[x_col], errors="coerce")
    valid_df = df.dropna(subset=[x_col]).sort_values(by=x_col)
    
    if color_col and color_col in valid_df.columns:
        agg_df = valid_df.groupby([x_col, color_col])[y_col].sum().reset_index()
        fig = px.line(agg_df, x=x_col, y=y_col, color=color_col, title=title or f"{y_col} Trend by {x_col}", markers=True)
    else:
        agg_df = valid_df.groupby(x_col)[y_col].sum().reset_index()
        fig = px.line(agg_df, x=x_col, y=y_col, title=title or f"{y_col} Trend by {x_col}", markers=True)
        
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    
    return {
        "chart_type": "line",
        "title": title or f"{y_col} Trend by {x_col}",
        "x_col": x_col,
        "y_col": y_col,
        "chart_spec": _serialize_plotly(fig),
        "summary": f"Generated line chart tracking {y_col} over {x_col}."
    }

def create_scatter_plot(file_path: str, x_col: str, y_col: str, color_col: Optional[str] = None, title: str = "") -> Dict[str, Any]:
    """Generates an interactive Plotly scatter plot."""
    df = load_dataset(file_path)
    
    if x_col not in df.columns or y_col not in df.columns:
        return {"error": f"Columns '{x_col}' or '{y_col}' not found."}
        
    fig = px.scatter(
        df, x=x_col, y=y_col, 
        color=color_col if color_col in df.columns else None,
        title=title or f"{y_col} vs {x_col}",
        trendline="ols" if pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_col]) else None
    )
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    
    return {
        "chart_type": "scatter",
        "title": title or f"{y_col} vs {x_col}",
        "x_col": x_col,
        "y_col": y_col,
        "chart_spec": _serialize_plotly(fig),
        "summary": f"Generated scatter plot comparing {y_col} against {x_col}."
    }

def create_box_plot(file_path: str, category_col: str, value_col: str, title: str = "") -> Dict[str, Any]:
    """Generates an interactive box plot for distribution comparison across categories."""
    df = load_dataset(file_path)
    
    if category_col not in df.columns or value_col not in df.columns:
        return {"error": f"Columns '{category_col}' or '{value_col}' not found."}
        
    fig = px.box(df, x=category_col, y=value_col, points="outliers", title=title or f"Distribution of {value_col} by {category_col}")
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    
    return {
        "chart_type": "box",
        "title": title or f"Distribution of {value_col} by {category_col}",
        "x_col": category_col,
        "y_col": value_col,
        "chart_spec": _serialize_plotly(fig),
        "summary": f"Generated box plot displaying distribution of {value_col} across {category_col} groups."
    }

def create_heatmap(file_path: str, title: str = "Correlation Heatmap") -> Dict[str, Any]:
    """Generates a correlation matrix heatmap for numerical features."""
    df = load_dataset(file_path)
    num_df = df.select_dtypes(include=[np.number])
    
    if num_df.empty:
        return {"error": "No numerical features for heatmap."}
        
    corr = num_df.corr().round(2)
    fig = px.imshow(corr, text_auto=True, color_continuous_scale="Viridis", title=title)
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    
    return {
        "chart_type": "heatmap",
        "title": title,
        "chart_spec": _serialize_plotly(fig),
        "summary": f"Generated correlation heatmap for {len(num_df.columns)} numerical columns."
    }
