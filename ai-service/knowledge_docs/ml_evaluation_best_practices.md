# Machine Learning Evaluation Best Practices

## 1. Train/Test Holdout & Validation Protocol
- **Data Splitting**: Always evaluate models on an independent 20% holdout test set (`test_size=0.20`).
- **Reproducibility**: Fix random seeds (`random_state=42`) across train/test splitting, estimator initialization, and feature transforms.
- **Leakage Prevention**: Fit scalers (StandardScaler) and categorical encoders (OneHotEncoder) strictly on the training partition and transform the test partition.
- **Identifier Exclusion**: Automatically exclude primary identifiers or surrogate keys (e.g. columns ending in `_id`, `ID`, `uuid`) from feature matrices.

## 2. Regression Model Evaluation
- **Mean Absolute Error (MAE)**: Measures average absolute prediction error in original target units. Robust against outliers.
- **Root Mean Squared Error (RMSE)**: Penalizes large prediction errors quadratically. Ideal for operational risk awareness.
- **Coefficient of Determination ($R^2$ Score)**: Proportion of target variance explained by predictor features.
  - $R^2 \approx 1.0$: Excellent predictive fit.
  - $R^2 < 0.0$: Severe model failure; indicates the model predicts worse than simply taking the target's empirical mean. Issue critical audit warning when negative.
- **Feature Importance**: For tree-based ensembles (Random Forest, Gradient Boosting), report the top 10 normalized Gini importance scores.

## 3. Classification Model Evaluation
- **Accuracy**: Overall fraction of correct predictions. Misleading under imbalanced class distributions.
- **Precision (Positive Predictive Value)**: $\frac{TP}{TP + FP}$. Crucial when false positives carry high cost.
- **Recall (Sensitivity)**: $\frac{TP}{TP + FN}$. Crucial for risk and churn mitigation where missing a positive case is costly.
- **$F_1$-Score**: Harmonic mean of Precision and Recall ($\frac{2 \times P \times R}{P + R}$). Best primary metric for imbalanced classes.
- **Confusion Matrix**: Full breakdown of True Negatives, False Positives, False Negatives, and True Positives.

## 4. Unsupervised Clustering Evaluation
- **Silhouette Score**: Evaluates cluster cohesion versus separation (ranging from $-1.0$ to $+1.0$):
  - $> 0.50$: Strong cluster structure
  - $0.25 - 0.50$: Moderate cluster structure
  - $< 0.25$: Weak or artificial clustering
- **Cluster Profiles**: Compute centroid mean feature values across each discovered cluster to provide interpretable business segment definitions.
