# Executive Reporting & Grounded Synthesis Guidelines

## 1. Transparency & Empirical Citation
- **Strict Grounding**: Every analytical claim in an executive report MUST be directly backed by an empirical tool observation.
- **Citation Reference**: Explicitly reference the tool name or observation index that yielded the finding (e.g., "[Observation: trend_analysis]", "[Observation: ttest]").
- **Zero Hallucination Rule**: Never assert numerical percentages, totals, or statistical $p$-values that do not exist in tool execution outputs.

## 2. Structure of an Executive Report
1. **Title**: Direct, professional summary statement of the question investigated.
2. **Executive Summary**: High-level synthesis outlining the scope, methodology, key findings, and validation audit status.
3. **Dataset Overview**: Dataset dimensions, column schema, missing percentage, and overall data quality score.
4. **Key Findings**: Bullet points stating primary empirical takeaways.
5. **Visual Insights**: Narrative summaries of generated charts accompanied by interactive chart specifications.
6. **Statistical Findings**: Detailed hypothesis testing outcomes ($t$-statistic, $F$-statistic, $\chi^2$, $p$-values, confidence intervals).
7. **Machine Learning Results**: Model performance metrics (accuracy, $R^2$, MAE, F1) and top feature importances (if ML was performed).
8. **Actionable Recommendations**: Business recommendations directly tied to empirical findings.
9. **Methodological Limitations & Caveats**: Explicitly note sample size constraints, observational limitations, and lack of causal proof.
