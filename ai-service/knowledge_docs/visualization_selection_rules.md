# Visualization Selection Rules & Design Standards

## 1. Core Principles of Visual Analysis
Visualizations transform raw distributions and numerical tables into immediate cognitive insights. Every selected visual must match variable data types and the analytical question.

## 2. Chart Selection Taxonomy
- **Line Charts (Trends & Time Series)**:
  - *Data Types*: Continuous chronological date/timestamp ($x$-axis) and continuous numerical metric ($y$-axis).
  - *Use Case*: Period-over-period performance, monthly/quarterly sales trajectory, growth monitoring.
  - *Optional Color Factor*: Categorical variable to display multi-series trend lines (e.g., region or product line).
- **Bar Charts (Categorical Comparison)**:
  - *Data Types*: Discrete categorical variable ($x$-axis) and aggregated continuous numerical metric ($y$-axis).
  - *Use Case*: Comparing total or average metrics across segments (e.g. revenue by region, sales by product category).
  - *Optional Grouping*: Secondary categorical variable for grouped or stacked comparisons.
- **Scatter Plots (Bivariate Relationships)**:
  - *Data Types*: Continuous numerical variable on both $x$-axis and $y$-axis.
  - *Use Case*: Inspecting bivariate linear or non-linear correlation, clustering patterns, or anomaly dispersion.
  - *Trendline*: Overlay Ordinary Least Squares (OLS) linear trendline to visualize relationship direction.
- **Box Plots (Distribution & Outlier Spread)**:
  - *Data Types*: Discrete categorical grouping ($x$-axis) and continuous numerical value ($y$-axis).
  - *Use Case*: Multi-group spread comparison, median alignment, interquartile range (IQR), and visual identification of extreme outliers.
- **Correlation Heatmaps (Multi-Variable Association)**:
  - *Data Types*: Full matrix of all continuous numerical columns in the dataset.
  - *Use Case*: Holistic feature screening, multicollinearity detection, and feature selection for modeling.

## 3. Visual Styling Standards
- Always use high-contrast, accessible dark palettes (`plotly_dark`).
- Include descriptive titles that state the analytical takeaway (e.g., "Quarterly Revenue Trend Showing Q3 Contraction" rather than generic "Revenue vs Date").
