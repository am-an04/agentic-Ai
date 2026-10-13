# Statistical Test Selection & Methodology Guide

## 1. Overview & Fundamental Rules
In empirical data analysis, statistical tests establish whether observed variations between groups or variables represent genuine population effects or random sampling noise.

- **Standard Significance Threshold**: A conventional significance level of $\alpha = 0.05$ is maintained. A $p$-value $< 0.05$ indicates statistical significance, rejecting the null hypothesis of no difference or no association.
- **Sample Size Considerations**: 
  - Central Limit Theorem assumptions generally hold when sample size $n \ge 30$.
  - When group sizes are below $n = 30$, tests are prone to low statistical power and increased risk of Type II errors.
  - For $n < 3$, statistical testing is unreliable and must be aborted or flagged.

## 2. Independent Two-Sample T-Test
- **When to Use**: Comparing the mean of a continuous numerical metric across exactly 2 distinct categorical groups.
- **Methodology**: Welch's two-sample t-test is preferred by default as it does not assume equal variances between the two groups.
- **Confidence Intervals**: Always report the 95% confidence interval for the difference between group means alongside the $t$-statistic and $p$-value.
- **Reporting Rule**: Specify group sample sizes ($n_1$, $n_2$), individual group means, absolute mean difference, and significance conclusion.

## 3. One-Way Analysis of Variance (ANOVA)
- **When to Use**: Comparing the mean of a continuous numerical metric across 3 or more categorical groups.
- **Hypotheses**: 
  - $H_0$: All group population means are equal ($\mu_1 = \mu_2 = \dots = \mu_k$).
  - $H_1$: At least one group mean is significantly different.
- **Test Metric**: Compute the $F$-statistic and associated $p$-value.
- **Reporting Rule**: Detail the overall $F$-statistic, $p$-value, and individual group mean breakdown to identify top-performing and lagging groups.

## 4. Chi-Square Test of Independence
- **When to Use**: Evaluating whether a statistically significant association exists between two categorical variables.
- **Requirements**: Data must be structured as a contingency table of cross-tabulated frequencies with at least 2 rows and 2 columns ($2 \times 2$ minimum).
- **Effect Size (Cramér's V)**: In addition to the $\chi^2$ statistic, degrees of freedom, and $p$-value, calculate Cramér's V ($0 \le V \le 1$) to quantify practical association strength:
  - $V < 0.10$: Negligible association
  - $0.10 \le V < 0.30$: Moderate association
  - $V \ge 0.30$: Strong association

## 5. Correlation vs. Causation Principle
- **Core Principle**: A high correlation coefficient ($r > 0.70$) indicates strong linear co-movement, NOT that variable $X$ causes variable $Y$.
- **Causal Language Prohibition**: Never use causal verbs such as *"drives"*, *"caused"*, *"led to"*, or *"impacted"* when interpreting observational data.
- **Prescribed Phrasing**: State *"Data indicates a strong positive/negative linear association"* or *"Variables exhibit significant co-occurrence"*.
