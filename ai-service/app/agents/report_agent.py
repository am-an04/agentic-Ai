"""
Report Generation Agent for DataPilot.
Uses LLM to synthesize grounded executive reports where every finding
strictly cites supporting empirical tool observations.
Falls back to deterministic template generation if LLM is unavailable.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.llm import LLMService, get_llm_service
from app.core.knowledge import retrieve_guidance_for_query

class GroundedFinding(BaseModel):
    finding: str = Field(description="Empirical finding with observation citation e.g. 'Quarterly revenue declined by 24.5% in Q3 [obs-1: trend_analysis]'")
    observation_refs: List[str] = Field(description="List of supporting observation IDs or tool names e.g. ['obs-1', 'trend_analysis']")

class GroundedReportSynthesis(BaseModel):
    title: str = Field(description="Professional executive report title")
    executive_summary: str = Field(description="High-level analytical summary grounded strictly in observation data")
    key_findings: List[GroundedFinding] = Field(description="List of empirical findings citing observation references")
    recommendations: List[str] = Field(description="Actionable business recommendations directly tied to findings")
    limitations: List[str] = Field(description="Data limitations, sample size constraints, and causal caveats")

class ReportGenerationAgent:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or get_llm_service()

    def generate_report(
        self,
        user_question: str,
        profile: Dict[str, Any],
        observations: List[Dict[str, Any]],
        charts: List[Dict[str, Any]],
        validation_result: Dict[str, Any],
        trace_logs: List[Dict[str, Any]],
        sources: Optional[List[str]] = None,
        retrieved_guidance: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes a structured, grounded analytical report using LLM reasoning
        with strict observation citation enforcement, falling back to rule-based logic on failure.
        """
        # Format structured findings from observations
        statistical_findings = []
        ml_results = None
        for obs in observations:
            tool_name = obs.get("tool_name", "")
            out_data = obs.get("output_data") or {}
            if tool_name in ["ttest", "chi_square", "anova"]:
                statistical_findings.append(out_data)
            if tool_name in ["train_regression", "train_classification", "train_clustering", "regression", "classification", "clustering"]:
                ml_results = out_data

        # Visual insights formatting
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

        # Try LLM Grounded Report Synthesis first
        llm_report = self._synthesize_with_llm(
            user_question=user_question,
            profile=profile,
            observations=observations,
            retrieved_guidance=retrieved_guidance
        )

        if llm_report:
            title = llm_report.title
            exec_summary = llm_report.executive_summary
            key_findings = [f.finding for f in llm_report.key_findings]
            recommendations = llm_report.recommendations
            limitations = llm_report.limitations
        else:
            # Fallback to deterministic template generation
            title, exec_summary, key_findings, recommendations, limitations = self._fallback_template_report(
                user_question=user_question,
                profile=profile,
                observations=observations,
                validation_result=validation_result
            )

        # Merge validation caveats if present
        if validation_result.get("correlation_vs_causation_warnings"):
            for w in validation_result["correlation_vs_causation_warnings"]:
                if w not in limitations:
                    limitations.append(w)

        report = {
            "title": title,
            "executive_summary": exec_summary,
            "dataset_overview": {
                "dataset_name": profile.get("dataset_name", "dataset"),
                "row_count": profile.get("row_count", 0),
                "col_count": profile.get("col_count", 0),
                "data_quality_score": profile.get("data_quality_score", 100),
                "numerical_columns": profile.get("numerical_columns", []),
                "categorical_columns": profile.get("categorical_columns", []),
                "date_columns": profile.get("date_columns", [])
            },
            "key_findings": key_findings[:8],
            "visual_insights": visual_insights,
            "statistical_findings": statistical_findings,
            "ml_results": ml_results,
            "recommendations": recommendations,
            "limitations": limitations,
            "analysis_trace": trace_logs,
            "created_at": datetime.now().isoformat(),
            "sources": sources or []
        }

        return report

    def _synthesize_with_llm(
        self,
        user_question: str,
        profile: Dict[str, Any],
        observations: List[Dict[str, Any]],
        retrieved_guidance: Optional[str] = None
    ) -> Optional[GroundedReportSynthesis]:
        """Calls the LLM to write a grounded report citing observation references."""
        if not observations:
            return None

        # Build numbered observation catalog
        obs_catalog = []
        for idx, obs in enumerate(observations, start=1):
            obs_id = f"obs-{idx}"
            tool = obs.get("tool_name", "unknown")
            summary = obs.get("summary", "")
            out_data = obs.get("output_data") or {}
            out_str = json.dumps(out_data)[:400]
            obs_catalog.append(f"[{obs_id}] Tool: '{tool}'\n  Summary: {summary}\n  Data: {out_str}")

        obs_text = "\n\n".join(obs_catalog)

        system_prompt = (
            "You are the DataPilot Lead Analytics Reporter. Your role is to write a rigorous, "
            "empirically grounded executive report answering the user's analytical question.\n\n"
            "STRICT GROUNDING RULES:\n"
            "1. You MUST use ONLY the tool observations provided below. Never invent external facts or numbers.\n"
            "2. Every finding in key_findings MUST cite its supporting observation reference (e.g. '[obs-1]').\n"
            "3. State associative relationships accurately; NEVER use causal verbs ('caused', 'drove', 'led to') "
            "   unless a controlled experiment design is confirmed.\n"
            "4. Recommendations must directly derive from the empirical findings.\n"
        )

        user_prompt = (
            f"User Analytical Question: \"{user_question}\"\n\n"
            f"Dataset Name: '{profile.get('dataset_name')}' ({profile.get('row_count')} rows, {profile.get('col_count')} columns)\n\n"
            f"Tool Observations Catalog:\n{obs_text}\n\n"
            f"{f'Methodology Guidelines:\n{retrieved_guidance}' if retrieved_guidance else ''}\n\n"
            "Synthesize the GroundedReportSynthesis object conforming strictly to the schema."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            llm_resp = self.llm_service.invoke(messages, response_schema=GroundedReportSynthesis)
            return llm_resp.parsed
        except Exception:
            # Graceful fallback to deterministic template
            return None

    def _fallback_template_report(
        self,
        user_question: str,
        profile: Dict[str, Any],
        observations: List[Dict[str, Any]],
        validation_result: Dict[str, Any]
    ) -> tuple[str, str, List[str], List[str], List[str]]:
        """Deterministic fallback report synthesis."""
        key_findings = []
        for idx, obs in enumerate(observations, start=1):
            summary = obs.get("summary", "")
            tool_name = obs.get("tool_name", "")
            if summary:
                key_findings.append(f"{summary} [obs-{idx}: {tool_name}]")

        exec_summary = (
            f"Autonomous analytical investigation for question: '{user_question}'. "
            f"Analyzed dataset '{profile.get('dataset_name')}' ({profile.get('row_count')} rows x {profile.get('col_count')} cols). "
            f"Completed {len(observations)} empirical tool executions across EDA, statistical testing, and visualization. "
            f"Validation audit status: {validation_result.get('summary', 'Audit complete')}."
        )

        recommendations = []
        if any("q3" in str(f).lower() or "drop" in str(f).lower() for f in key_findings) or "sales" in user_question.lower():
            recommendations.append("Investigate high discount rates on underperforming products to protect margin.")
            recommendations.append("Prioritize sales enablement in regions exhibiting period-over-period decline.")
        else:
            recommendations.append("Monitor high-cardinality categorical segments for targeted promotional campaigns.")
            recommendations.append("Standardize data collection to reduce missing values and outlier anomalies.")

        limitations = [
            f"Analysis is constrained to the {profile.get('row_count')} records present in '{profile.get('dataset_name')}'.",
            "Observational data indicates empirical association rather than confirmed causal direction.",
            "Predictions and segmentations are subject to data sample distribution limitations."
        ]

        title = f"DataPilot Autonomous Analysis: {user_question}"
        return title, exec_summary, key_findings, recommendations, limitations
