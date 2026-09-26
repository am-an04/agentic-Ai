import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix,
    silhouette_score
)
from app.tools.profiling_tools import load_dataset

def build_preprocessor(df: pd.DataFrame, feature_cols: List[str]):
    """Constructs scikit-learn ColumnTransformer for automatic imputing and encoding."""
    num_cols = [c for c in feature_cols if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in feature_cols if c not in num_cols]
    
    num_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    cat_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', num_transformer, num_cols),
            ('cat', cat_transformer, cat_cols)
        ]
    )
    return preprocessor, num_cols, cat_cols

def train_regression_model(file_path: str, target_col: str, feature_cols: Optional[List[str]] = None, model_type: str = "random_forest") -> Dict[str, Any]:
    """Trains a regression model to predict a continuous numerical variable."""
    df = load_dataset(file_path)
    
    if target_col not in df.columns:
        return {"error": f"Target column '{target_col}' not found in dataset."}
        
    if not feature_cols:
        feature_cols = [c for c in df.columns if c != target_col and not c.lower().endswith('_id')]
        
    valid_df = df.dropna(subset=[target_col])
    X = valid_df[feature_cols]
    y = valid_df[target_col]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    preprocessor, num_cols, cat_cols = build_preprocessor(valid_df, feature_cols)
    
    if model_type == "linear":
        model = LinearRegression()
    elif model_type == "gradient_boosting":
        model = GradientBoostingRegressor(random_state=42)
    else:
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('regressor', model)])
    pipeline.fit(X_train, y_train)
    
    y_pred = pipeline.predict(X_test)
    
    mae = float(mean_absolute_error(y_test, y_pred))
    mse = float(mean_squared_error(y_test, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_test, y_pred))
    
    # Feature importances if tree model
    importances = {}
    if hasattr(model, "feature_importances_"):
        # get feature names out
        try:
            cat_encoder = pipeline.named_steps['preprocessor'].named_transformers_['cat'].named_steps['encoder']
            encoded_cat_cols = list(cat_encoder.get_feature_names_out(cat_cols)) if cat_cols else []
            all_feature_names = num_cols + encoded_cat_cols
            fi = model.feature_importances_
            importances = {name: float(round(score, 4)) for name, score in zip(all_feature_names, fi)}
            # sort
            importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True)[:10])
        except Exception:
            pass

    return {
        "task": "regression",
        "model_type": model_type,
        "target_col": target_col,
        "features_used": feature_cols,
        "metrics": {
            "mae": round(mae, 4),
            "mse": round(mse, 4),
            "rmse": round(rmse, 4),
            "r2_score": round(r2, 4)
        },
        "top_feature_importances": importances,
        "summary": f"Trained {model_type} regression model on '{target_col}'. Test R² Score: {r2:.3f}, MAE: {mae:.2f}, RMSE: {rmse:.2f}."
    }

def train_classification_model(file_path: str, target_col: str, feature_cols: Optional[List[str]] = None, model_type: str = "random_forest") -> Dict[str, Any]:
    """Trains a classification model to predict a discrete target variable."""
    df = load_dataset(file_path)
    
    if target_col not in df.columns:
        return {"error": f"Target column '{target_col}' not found in dataset."}
        
    if not feature_cols:
        feature_cols = [c for c in df.columns if c != target_col and not c.lower().endswith('_id')]
        
    valid_df = df.dropna(subset=[target_col])
    X = valid_df[feature_cols]
    y = valid_df[target_col]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    preprocessor, num_cols, cat_cols = build_preprocessor(valid_df, feature_cols)
    
    if model_type == "logistic":
        model = LogisticRegression(max_iter=1000)
    elif model_type == "gradient_boosting":
        model = GradientBoostingClassifier(random_state=42)
    else:
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', model)])
    pipeline.fit(X_train, y_train)
    
    y_pred = pipeline.predict(X_test)
    
    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, average='weighted', zero_division=0))
    rec = float(recall_score(y_test, y_pred, average='weighted', zero_division=0))
    f1 = float(f1_score(y_test, y_pred, average='weighted', zero_division=0))
    cm = confusion_matrix(y_test, y_pred).tolist()
    
    # Feature importances
    importances = {}
    if hasattr(model, "feature_importances_"):
        try:
            cat_encoder = pipeline.named_steps['preprocessor'].named_transformers_['cat'].named_steps['encoder']
            encoded_cat_cols = list(cat_encoder.get_feature_names_out(cat_cols)) if cat_cols else []
            all_feature_names = num_cols + encoded_cat_cols
            fi = model.feature_importances_
            importances = {name: float(round(score, 4)) for name, score in zip(all_feature_names, fi)}
            importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True)[:10])
        except Exception:
            pass

    return {
        "task": "classification",
        "model_type": model_type,
        "target_col": target_col,
        "features_used": feature_cols,
        "metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "confusion_matrix": cm
        },
        "top_feature_importances": importances,
        "summary": f"Trained {model_type} classification model on '{target_col}'. Accuracy: {acc:.3f}, F1-Score: {f1:.3f}."
    }

def train_clustering_model(file_path: str, feature_cols: Optional[List[str]] = None, n_clusters: int = 3) -> Dict[str, Any]:
    """Segments data using K-Means clustering."""
    df = load_dataset(file_path)
    
    if not feature_cols:
        feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [c for c in feature_cols if not c.lower().endswith('_id')]
        
    if len(feature_cols) < 2:
        return {"error": "Clustering requires at least 2 numerical feature columns."}
        
    valid_df = df[feature_cols].dropna()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(valid_df)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    
    sil_score = float(silhouette_score(X_scaled, cluster_labels)) if len(valid_df) > n_clusters else 0.0
    
    valid_df['cluster'] = cluster_labels
    cluster_means = valid_df.groupby('cluster').mean().round(2).to_dict(orient="index")
    cluster_counts = valid_df['cluster'].value_counts().to_dict()
    
    return {
        "task": "clustering",
        "model_type": "k_means",
        "n_clusters": n_clusters,
        "features_used": feature_cols,
        "metrics": {
            "silhouette_score": round(sil_score, 4)
        },
        "cluster_counts": {str(k): int(v) for k, v in cluster_counts.items()},
        "cluster_profiles": {str(k): v for k, v in cluster_means.items()},
        "summary": f"Trained K-Means model with {n_clusters} clusters. Silhouette Score: {sil_score:.3f}."
    }
