import os
import pytest
from unittest.mock import MagicMock, patch
from app.agents.orchestrator import AgentOrchestrator, ReflectionDecision
from app.agents.planner import LLMPlanner
from app.core.llm import LLMService, LLMResponse
from app.models.schemas import AnalysisPlan, PlanStep

@pytest.fixture
def dataset_csv():
    # Absolute path to sales_churn_analytics.csv
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.abspath(os.path.join(base_dir, "..", "..", "datasets", "sales_churn_analytics.csv"))
    assert os.path.exists(csv_path), f"Dataset not found at {csv_path}"
    return csv_path

def test_graph_nodes_exist():
    orchestrator = AgentOrchestrator()
    assert orchestrator.graph is not None
    # LangGraph compiled graph should have the expected nodes
    node_names = list(orchestrator.graph.get_graph().nodes.keys())
    assert "profile" in node_names
    assert "plan" in node_names
    assert "execute_step" in node_names
    assert "reflect" in node_names
    assert "validate" in node_names
    assert "report" in node_names

def test_full_analysis_workflow(dataset_csv):
    """Tests end-to-end execution of the LangGraph agent loop without ML human approval."""
    orchestrator = AgentOrchestrator()
    initial_state = {
        "dataset_path": dataset_csv,
        "user_question": "Analyze sales revenue trends",
        "session_id": "test-session-e2e",
        "profile": None,
        "plan": None,
        "current_step_idx": 0,
        "observations": [],
        "charts": [],
        "requires_human_approval": False,
        "approval_prompt": None,
        "is_approved": False,
        "validation_result": None,
        "final_report": None,
        "trace_logs": [],
        "errors": [],
        "completed": False,
        "enable_ml": False
    }

    final_state = orchestrator.run_analysis(initial_state)

    assert final_state["completed"] is True
    assert final_state["profile"] is not None
    assert final_state["plan"] is not None
    assert len(final_state["observations"]) > 0
    assert final_state["validation_result"] is not None
    assert final_state["final_report"] is not None
    assert len(final_state["trace_logs"]) > 0

    # Ensure all intermediate steps completed
    for step in final_state["plan"]["plan_steps"]:
        assert step["status"] in ["completed", "skipped"]

def test_human_in_the_loop_approval_pause_and_resume(dataset_csv):
    """Tests that ML steps pause for human confirmation and resume cleanly once approved."""
    orchestrator = AgentOrchestrator()
    session_id = "test-session-hitl"

    initial_state = {
        "dataset_path": dataset_csv,
        "user_question": "Predict churn risk using machine learning",
        "session_id": session_id,
        "profile": None,
        "plan": None,
        "current_step_idx": 0,
        "observations": [],
        "charts": [],
        "requires_human_approval": False,
        "approval_prompt": None,
        "is_approved": False,
        "validation_result": None,
        "final_report": None,
        "trace_logs": [],
        "errors": [],
        "completed": False,
        "enable_ml": True
    }

    # First invocation should pause at ML step requiring human confirmation
    paused_state = orchestrator.run_analysis(initial_state)

    assert paused_state["requires_human_approval"] is True
    assert paused_state["approval_prompt"] is not None
    assert "Proceed with Machine Learning" in paused_state["approval_prompt"]
    assert paused_state["completed"] is False

    # Simulate user approval in /api/approve
    paused_state["is_approved"] = True
    paused_state["requires_human_approval"] = False

    resumed_state = orchestrator.run_analysis(paused_state)

    assert resumed_state["completed"] is True
    assert resumed_state["final_report"] is not None
    # Check that an ML observation was produced
    ml_obs = [obs for obs in resumed_state["observations"] if "train_" in obs.get("tool_name", "")]
    assert len(ml_obs) > 0

def test_reflect_node_budget_enforcement(dataset_csv):
    """Tests that reflect node respects max step budget and halts runaway execution."""
    orchestrator = AgentOrchestrator()
    # Set tight budget of 2 observations
    initial_state = {
        "dataset_path": dataset_csv,
        "user_question": "Investigate revenue and categories",
        "session_id": "test-budget-enforcement",
        "profile": None,
        "plan": None,
        "current_step_idx": 0,
        "observations": [],
        "charts": [],
        "requires_human_approval": False,
        "approval_prompt": None,
        "is_approved": False,
        "validation_result": None,
        "final_report": None,
        "trace_logs": [],
        "errors": [],
        "completed": False,
        "enable_ml": False,
        "step_budget": 2
    }

    final_state = orchestrator.run_analysis(initial_state)

    assert final_state["completed"] is True
    assert len(final_state["observations"]) <= 2
    # Ensure budget limit log was recorded
    budget_logs = [t for t in final_state["trace_logs"] if "Budget" in t["step"]]
    assert len(budget_logs) > 0

def test_reflect_node_adds_adaptive_step(dataset_csv):
    """Tests that reflect node can dynamically insert a follow-up step into the plan."""
    mock_llm = MagicMock(spec=LLMService)
    # Mock reflection returning an adaptive add_step decision
    mock_llm.invoke.return_value = LLMResponse(
        content="{\"decision\": \"add_step\"}",
        parsed=ReflectionDecision(
            decision="add_step",
            reasoning="Observed skewness; adding distribution analysis of revenue",
            action="Investigate Revenue Skew",
            description="Deep dive on revenue distribution",
            tool_needed="distribution_analysis",
            params={"column": "revenue"}
        ),
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150
    )

    orchestrator = AgentOrchestrator(llm_service=mock_llm)
    state = {
        "dataset_path": dataset_csv,
        "user_question": "What is the revenue trend?",
        "session_id": "test-reflect-adaptive",
        "profile": {
            "columns": ["order_date", "revenue", "region"],
            "numerical_columns": ["revenue"],
            "categorical_columns": ["region"],
            "date_columns": ["order_date"]
        },
        "plan": {
            "goal": "Test plan",
            "plan_steps": [
                {"step_number": 1, "action": "Profile", "tool_needed": "profile_dataset", "status": "completed"},
                {"step_number": 2, "action": "Validate", "tool_needed": "validate_claims", "status": "pending"},
                {"step_number": 3, "action": "Report", "tool_needed": "generate_report", "status": "pending"}
            ]
        },
        "observations": [
            {"tool_name": "trend_analysis", "summary": "Detected 30% drop in revenue", "output_data": {"drop": 30}}
        ],
        "trace_logs": [],
        "step_budget": 10
    }

    result = orchestrator._node_reflect(state)

    plan_steps = result["plan"]["plan_steps"]
    tool_names = [s["tool_needed"] for s in plan_steps]
    assert "distribution_analysis" in tool_names
    # Check that trace log recorded the adaptive step
    trace = [t for t in result["trace_logs"] if "Adaptive Step Added" in t["step"]]
    assert len(trace) > 0
