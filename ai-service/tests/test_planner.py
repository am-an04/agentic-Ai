import pytest
import json
from unittest.mock import MagicMock, patch
from app.models.schemas import AnalysisPlan, PlanStep
from app.tools.catalog import TOOL_CATALOG, resolve_tool_name
from app.agents.planner import (
    LLMPlanner,
    sanitize_and_repair_plan,
    _fuzzy_match_column
)
from app.agents.orchestrator import AgentOrchestrator
from app.core.llm import LLMService, LLMResponse

@pytest.fixture
def sample_profile():
    return {
        "dataset_name": "sales_churn.csv",
        "row_count": 1000,
        "col_count": 6,
        "columns": ["customer_id", "monthly_charges", "total_charges", "churn_risk", "contract_type", "signup_date"],
        "numerical_columns": ["monthly_charges", "total_charges"],
        "categorical_columns": ["churn_risk", "contract_type"],
        "date_columns": ["signup_date"],
        "potential_targets": ["churn_risk"],
        "data_quality_score": 98.5,
        "data_quality_issues": []
    }

def test_tool_catalog_and_aliases():
    # Verify canonical tools exist
    assert "correlation_analysis" in TOOL_CATALOG
    assert "trend_analysis" in TOOL_CATALOG
    assert "ttest" in TOOL_CATALOG
    assert "train_classification" in TOOL_CATALOG

    # Verify alias resolution
    assert resolve_tool_name("linear_regression") == "train_regression"
    assert resolve_tool_name("two_sample_ttest") == "ttest"
    assert resolve_tool_name("kmeans") == "train_clustering"
    assert resolve_tool_name("barchart") == "bar_chart"

def test_fuzzy_match_column():
    valid = ["Monthly_Charges", "contract_type", "churn_risk"]
    assert _fuzzy_match_column("monthly_charges", valid) == "Monthly_Charges"
    assert _fuzzy_match_column("contract", valid) == "contract_type"
    assert _fuzzy_match_column("nonexistent", valid) is None

def test_sanitize_and_repair_plan(sample_profile):
    raw_plan = AnalysisPlan(
        goal="Identify drivers of churn",
        plan_steps=[
            PlanStep(
                step_number=1,
                action="Explore Churn",
                description="Check churn distribution",
                tool_needed="distribution_analysis",
                params={"column": "churn_risk"}
            ),
            PlanStep(
                step_number=2,
                action="Train Random Forest",
                description="Classify churn",
                tool_needed="random_forest",  # alias for train_classification
                params={"target_col": "churn_risk", "feature_cols": ["monthly_charges", "fake_col"]}
            ),
            PlanStep(
                step_number=3,
                action="Hallucinated Action",
                description="Use non-existent tool",
                tool_needed="super_deep_learning_magic",  # unknown tool
                params={}
            )
        ],
        reasoning="Multi-step churn analysis plan."
    )

    repaired = sanitize_and_repair_plan(raw_plan, sample_profile, enable_ml=True)
    steps = repaired["plan_steps"]

    # Step 1 must be profiling
    assert steps[0]["tool_needed"] == "profile_dataset"
    assert steps[0]["status"] == "completed"

    # Step 2 distribution_analysis preserved
    assert steps[1]["tool_needed"] == "distribution_analysis"
    assert steps[1]["params"]["column"] == "churn_risk"

    # Step 3 train_classification repaired from alias, requires approval, fake_col stripped
    assert steps[2]["tool_needed"] == "train_classification"
    assert steps[2]["requires_approval"] is True
    assert "fake_col" not in steps[2]["params"]["feature_cols"]
    assert "monthly_charges" in steps[2]["params"]["feature_cols"]

    # Non-existent tool was dropped
    tool_names = [s["tool_needed"] for s in steps]
    assert "super_deep_learning_magic" not in tool_names

    # Ensure validation and report generation are present at end
    assert steps[-2]["tool_needed"] == "validate_claims"
    assert steps[-1]["tool_needed"] == "generate_report"

    # Sequential numbering
    for i, s in enumerate(steps, start=1):
        assert s["step_number"] == i

def test_sanitize_plan_drops_ml_when_disabled(sample_profile):
    raw_plan = AnalysisPlan(
        goal="Inspect numbers only",
        plan_steps=[
            PlanStep(
                step_number=1,
                action="Train Classifier",
                description="Classify",
                tool_needed="train_classification",
                params={"target_col": "churn_risk"}
            )
        ],
        reasoning="Test disabling ML"
    )

    repaired = sanitize_and_repair_plan(raw_plan, sample_profile, enable_ml=False)
    tools = [s["tool_needed"] for s in repaired["plan_steps"]]
    assert "train_classification" not in tools

def test_llm_planner_generate_plan(sample_profile):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm_response = LLMResponse(
        content="{\"goal\": \"Investigate churn\", \"plan_steps\": [], \"reasoning\": \"Fast plan\"}",
        parsed=AnalysisPlan(
            goal="Investigate churn risk factors",
            plan_steps=[
                PlanStep(
                    step_number=1,
                    action="Analyze Group Difference",
                    description="Group by contract type",
                    tool_needed="group_by_analysis",
                    params={"group_col": "contract_type", "target_col": "monthly_charges"}
                )
            ],
            reasoning="Group analysis will show churn contrast"
        ),
        prompt_tokens=250,
        completion_tokens=90,
        total_tokens=340,
        estimated_cost_usd=0.0001,
        latency_ms=250.0,
        provider="gemini",
        model="gemini-2.5-flash"
    )
    mock_llm.invoke.return_value = mock_llm_response

    planner = LLMPlanner(llm_service=mock_llm)
    plan, trace = planner.generate_plan(
        question="Why are customers churning?",
        profile=sample_profile,
        enable_ml=True
    )

    assert plan["goal"] == "Investigate churn risk factors"
    assert len(plan["plan_steps"]) >= 4  # profile, group_by, validate, report
    assert trace["step"] == "LLM Analytical Planner"
    assert trace["llm_usage"]["total_tokens"] == 340

def test_orchestrator_create_plan_fallback(sample_profile):
    """Verifies that orchestrator falls back to rule-based planner if LLM planner fails."""
    mock_planner = MagicMock(spec=LLMPlanner)
    mock_planner.generate_plan.side_effect = RuntimeError("API key invalid / connection timeout")

    orchestrator = AgentOrchestrator(planner=mock_planner)
    trace_logs = []

    plan = orchestrator.create_plan(
        question="Analyze Q3 sales revenue decline",
        profile=sample_profile,
        trace_logs=trace_logs
    )

    assert plan is not None
    assert len(plan["plan_steps"]) > 0
    # Check that fallback was logged into trace_logs
    fallback_entries = [t for t in trace_logs if t["step"] == "Planner Fallback"]
    assert len(fallback_entries) == 1
    assert "Falling back to deterministic rule-based planner" in fallback_entries[0]["description"]
