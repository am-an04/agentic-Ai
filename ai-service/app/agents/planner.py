"""
LLM-Powered Dynamic Planner Agent for DataPilot.
Replaces keyword-matching rules with multi-turn LLM reasoning, tool catalog validation,
and column schema verification against dataset profile.
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from app.models.schemas import AnalysisPlan, PlanStep
from app.tools.catalog import TOOL_CATALOG, resolve_tool_name
from app.core.llm import LLMService, get_llm_service

def _fuzzy_match_column(col_name: str, valid_cols: List[str]) -> Optional[str]:
    """Finds exact or case-insensitive match for a column name."""
    if not col_name or not valid_cols:
        return None
    if col_name in valid_cols:
        return col_name
    col_lower = col_name.strip().lower()
    for vc in valid_cols:
        if vc.lower() == col_lower:
            return vc
    # Check substring containment
    for vc in valid_cols:
        if col_lower in vc.lower() or vc.lower() in col_lower:
            return vc
    return None

def sanitize_and_repair_plan(
    plan: AnalysisPlan,
    profile: Dict[str, Any],
    enable_ml: bool = True
) -> Dict[str, Any]:
    """
    Validates, repairs, and sanitizes an LLM-generated plan:
    - Resolves tool names against TOOL_CATALOG (drops unknown tools)
    - Verifies column parameters against actual profile columns
    - Enforces human approval on ML steps and respects enable_ml flag
    - Ensures sequential step numbering and final validation/report steps
    """
    valid_cols = profile.get("columns", [])
    num_cols = profile.get("numerical_columns", [])
    cat_cols = profile.get("categorical_columns", [])
    date_cols = profile.get("date_columns", [])

    repaired_steps: List[Dict[str, Any]] = []

    # 1. Step 1 is always profiling (already completed)
    repaired_steps.append({
        "step_number": 1,
        "action": "Profile Dataset",
        "description": f"Inspected dataset shape ({profile.get('row_count', 0)} rows x {profile.get('col_count', 0)} cols) and data quality score ({profile.get('data_quality_score', 100):.1f}%).",
        "tool_needed": "profile_dataset",
        "params": {},
        "status": "completed",
        "requires_approval": False
    })

    for step in plan.plan_steps:
        tool_raw = step.tool_needed
        if not tool_raw or tool_raw == "profile_dataset":
            continue

        tool_canonical = resolve_tool_name(tool_raw)
        if tool_canonical not in TOOL_CATALOG:
            # Unknown tool, skip
            continue

        # If ML is disabled, skip ML tools
        is_ml_tool = TOOL_CATALOG[tool_canonical]["category"] == "ml"
        if is_ml_tool and not enable_ml:
            continue

        params = step.params or {}
        repaired_params: Dict[str, Any] = {}
        step_is_valid = True

        # Validate column arguments in params
        for p_key, p_val in params.items():
            if p_key in ["group_col", "col1", "category_col", "color_col"]:
                if isinstance(p_val, str):
                    matched = _fuzzy_match_column(p_val, valid_cols)
                    if matched:
                        repaired_params[p_key] = matched
                    elif cat_cols:
                        repaired_params[p_key] = cat_cols[0]
                    else:
                        step_is_valid = False
            elif p_key in ["target_col", "value_col", "y_col"]:
                if isinstance(p_val, str):
                    matched = _fuzzy_match_column(p_val, valid_cols)
                    if matched:
                        repaired_params[p_key] = matched
                    elif num_cols:
                        repaired_params[p_key] = num_cols[0]
                    else:
                        step_is_valid = False
            elif p_key in ["date_col"]:
                if isinstance(p_val, str):
                    matched = _fuzzy_match_column(p_val, valid_cols)
                    if matched:
                        repaired_params[p_key] = matched
                    elif date_cols:
                        repaired_params[p_key] = date_cols[0]
                    else:
                        step_is_valid = False
            elif p_key in ["x_col"]:
                if isinstance(p_val, str):
                    matched = _fuzzy_match_column(p_val, valid_cols)
                    if matched:
                        repaired_params[p_key] = matched
                    elif tool_canonical == "line_chart" and date_cols:
                        repaired_params[p_key] = date_cols[0]
                    elif tool_canonical == "bar_chart" and cat_cols:
                        repaired_params[p_key] = cat_cols[0]
                    elif num_cols:
                        repaired_params[p_key] = num_cols[0]
                    else:
                        step_is_valid = False
            elif p_key in ["columns", "feature_cols"]:
                if isinstance(p_val, list):
                    filtered_cols = [c for c in p_val if c in valid_cols or _fuzzy_match_column(c, valid_cols)]
                    repaired_params[p_key] = [
                        _fuzzy_match_column(c, valid_cols) or c for c in filtered_cols
                    ]
            else:
                repaired_params[p_key] = p_val

        # Tool-specific minimum requirement checks
        if tool_canonical == "trend_analysis" and not date_cols:
            step_is_valid = False
        if tool_canonical == "correlation_analysis" and len(num_cols) < 2:
            step_is_valid = False

        if not step_is_valid:
            continue

        # Prevent duplicate validate_claims or generate_report in the middle
        if tool_canonical in ["validate_claims", "generate_report"]:
            continue

        repaired_steps.append({
            "step_number": len(repaired_steps) + 1,
            "action": step.action,
            "description": step.description,
            "tool_needed": tool_canonical,
            "params": repaired_params,
            "status": "pending",
            "requires_approval": is_ml_tool
        })

    # Ensure validation step exists
    repaired_steps.append({
        "step_number": len(repaired_steps) + 1,
        "action": "Validate Findings",
        "description": "Perform empirical observation audit, anti-hallucination check, and correlation vs causation audit.",
        "tool_needed": "validate_claims",
        "params": {},
        "status": "pending",
        "requires_approval": False
    })

    # Ensure final report generation step exists
    repaired_steps.append({
        "step_number": len(repaired_steps) + 1,
        "action": "Generate Report",
        "description": "Synthesize final structured executive report with insights and recommendations.",
        "tool_needed": "generate_report",
        "params": {},
        "status": "pending",
        "requires_approval": False
    })

    # Re-number all steps sequentially
    for idx, s in enumerate(repaired_steps, start=1):
        s["step_number"] = idx

    return {
        "goal": plan.goal,
        "plan_steps": repaired_steps,
        "reasoning": plan.reasoning
    }

class LLMPlanner:
    """Agent that creates structured, context-aware analysis plans using an LLM."""

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or get_llm_service()

    def generate_plan(
        self,
        question: str,
        profile: Dict[str, Any],
        enable_ml: bool = True,
        retrieved_guidance: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Creates an analytical plan using LLM reasoning and the tool catalog.
        Returns (plan_dict, trace_log_entry).
        Raises Exception if the LLM call or plan generation fails unrecoverably.
        """
        # Format profile summary without sending raw rows
        profile_summary = {
            "dataset_name": profile.get("dataset_name", "dataset"),
            "row_count": profile.get("row_count", 0),
            "col_count": profile.get("col_count", 0),
            "columns": profile.get("columns", []),
            "numerical_columns": profile.get("numerical_columns", []),
            "categorical_columns": profile.get("categorical_columns", []),
            "date_columns": profile.get("date_columns", []),
            "potential_targets": profile.get("potential_targets", []),
            "data_quality_score": profile.get("data_quality_score", 100),
            "data_quality_issues": profile.get("data_quality_issues", [])
        }

        # Catalog summary for the prompt
        catalog_summary = {}
        for tool_name, meta in TOOL_CATALOG.items():
            if meta["category"] == "ml" and not enable_ml:
                continue
            catalog_summary[tool_name] = {
                "description": meta["description"],
                "parameters": meta["parameters"]
            }

        guidance_text = f"\nAnalytical Methodology Guidance:\n{retrieved_guidance}\n" if retrieved_guidance else ""

        system_prompt = (
            "You are the DataPilot Lead AI Planning Agent. Your role is to formulate a rigorous, "
            "step-by-step data analysis plan to answer the user's analytical question.\n\n"
            "CRITICAL CONSTRAINTS:\n"
            "1. You MUST ONLY use tools available in the TOOL_CATALOG provided below.\n"
            "2. NEVER invent tool names or parameters.\n"
            "3. Every column name used in tool parameters MUST exist in the dataset profile.\n"
            "4. Never hallucinate column names.\n"
            "5. Structure the plan logically:\n"
            "   - Exploratory data analysis (trends, groupings, distributions, correlations)\n"
            "   - Statistical testing (t-test, ANOVA, or chi-square where appropriate)\n"
            "   - Machine Learning models (only if enable_ml is true and relevant to prediction/clustering)\n"
            "   - High-impact visualizations (bar chart, line chart, scatter plot, heatmap)\n"
            "   - Validate claims and generate report.\n"
        )

        user_prompt = (
            f"User Analytical Question: \"{question}\"\n\n"
            f"Dataset Profile:\n{json.dumps(profile_summary, indent=2)}\n\n"
            f"Available Tool Catalog:\n{json.dumps(catalog_summary, indent=2)}\n"
            f"{guidance_text}\n"
            f"ML Models Enabled: {enable_ml}\n\n"
            "Create a goal-oriented AnalysisPlan adhering strictly to the schema."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        llm_resp = self.llm_service.invoke(messages, response_schema=AnalysisPlan)
        plan_obj: AnalysisPlan = llm_resp.parsed

        # Sanitize and verify column references against profile
        final_plan = sanitize_and_repair_plan(plan_obj, profile, enable_ml=enable_ml)

        trace_log = llm_resp.to_trace_log("LLM Analytical Planner")
        trace_log["description"] = (
            f"LLM Planner formulated {len(final_plan['plan_steps'])}-step strategy using {llm_resp.provider}:{llm_resp.model}. "
            f"Goal: '{final_plan['goal']}'"
        )

        return final_plan, trace_log
