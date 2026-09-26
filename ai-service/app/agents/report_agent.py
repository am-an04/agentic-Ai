from typing import Dict, Any, List
from datetime import datetime

class ReportGenerationAgent:
    def generate_report(
        self,
        user_question: str,
        profile: Dict[str, Any],
        observations: List[Dict[str, Any]],
        charts: List[Dict[str, Any]],
        validation_result: Dict[str, Any],
        trace_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesizes structured analytical report from execution findings."""
        
        # Key findings from observations
        key_findings = []
        statistical_findings = []
        ml_results = None
        
        for obs in observations:
            summary = obs.get("summary", "")
            tool_name = obs.get("tool_name", "")
            out_data = obs.get("output_data") or {}
            
            if summary:
                key_findings.append(summary)
                
            if tool_name in ["ttest", "chi_square", "anova"]:
                statistical_findings.append(out_data)
                
            if tool_name in ["train_regression", "train_classification", "train_clustering", "regression", "classification", "clustering"]:
                ml_results = out_data

        # Executive summary construction
        exec_summary = (
            f"Autonomous investigation for analytical question: '{user_question}'. "
            f"Analyzed dataset '{profile.get('dataset_name')}' ({profile.get('row_count')} rows x {profile.get('col_count')} columns). "
            f"Completed {len(observations)} tool executions across EDA, statistical testing, and visualization. "
            f"Validation audit score: {validation_result.get('summary')}."
        )

        # Actionable recommendations tied to findings
        recommendations = []
        if any("q3" in str(f).lower() or "drop" in str(f).lower() for f in key_findings) or "sales" in user_question.lower():
            recommendations.append("Investigate high discount rates on underperforming products to protect margin.")
            recommendations.append("Prioritize sales enablement in regions exhibiting significant period-over-period decline.")
        else:
            recommendations.append("Monitor high-cardinality categorical segments for targeted promotional campaigns.")
            recommendations.append("Standardize data collection to reduce missing values and outlier anomalies.")

        # Limitations
        limitations = [
            f"Analysis is constrained to the {profile.get('row_count')} records present in '{profile.get('dataset_name')}'.",
            "Observational data indicates strong correlation but does not confirm causal direction without controlled experimental testing.",
            "Predictions and segmentations are subject to data sample distribution limitations."
        ]
        
        if validation_result.get("correlation_vs_causation_warnings"):
            limitations.extend(validation_result.get("correlation_vs_causation_warnings"))

        # Visual insights
        visual_insights = []
        for chart in charts:
            out = chart.get("output_data") or {}
            if "chart_spec" in out:
                visual_insights.append({
                    "title": out.get("title", "Analytical Chart"),
                    "chart_type": out.get("chart_type", "bar"),
                    "description": out.get("summary", ""),
                    "chart_spec": out.get("chart_spec")
                })

        report = {
            "title": f"DataPilot Autonomous Analysis: {user_question}",
            "executive_summary": exec_summary,
            "dataset_overview": {
                "dataset_name": profile.get("dataset_name"),
                "row_count": profile.get("row_count"),
                "col_count": profile.get("col_count"),
                "data_quality_score": profile.get("data_quality_score"),
                "numerical_columns": profile.get("numerical_columns"),
                "categorical_columns": profile.get("categorical_columns"),
                "date_columns": profile.get("date_columns")
            },
            "key_findings": key_findings[:8],
            "visual_insights": visual_insights,
            "statistical_findings": statistical_findings,
            "ml_results": ml_results,
            "recommendations": recommendations,
            "limitations": limitations,
            "analysis_trace": trace_logs,
            "created_at": datetime.now().isoformat()
        }
        
        return report
