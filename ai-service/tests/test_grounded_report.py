import pytest
from unittest.mock import MagicMock
from app.agents.report_agent import ReportGenerationAgent, GroundedReportSynthesis, GroundedFinding
from app.agents.validation_agent import (
    ValidationAgent,
    extract_numbers_from_text,
    find_number_in_payload,
    LLMVerificationAudit,
    ClaimAuditItem
)
from app.core.llm import LLMService, LLMResponse

def test_extract_numbers_and_payload_matching():
    text = "Revenue declined by 24.5% in Q3 reaching a total of 1200.0."
    num_tuples = extract_numbers_from_text(text)
    nums = [n for n, _ in num_tuples]
    assert 24.5 in nums
    assert 1200.0 in nums
    assert 3.0 not in nums

    payload = {
        "metrics": {"total_revenue": 1200.0, "pct_change": -24.5},
        "details": [{"period": "2025-Q3", "val": 350.0}]
    }

    assert find_number_in_payload(1200.0, payload) is True
    assert find_number_in_payload(24.5, payload) is True
    assert find_number_in_payload(999.0, payload) is False

def test_report_agent_llm_synthesis():
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.invoke.return_value = LLMResponse(
        content="{\"title\": \"Grounded Report\"}",
        parsed=GroundedReportSynthesis(
            title="Analysis of Sales Contraction",
            executive_summary="Empirical investigation revealed a 24.5% quarterly decrease in revenue.",
            key_findings=[
                GroundedFinding(
                    finding="Quarterly revenue dropped 24.5% in Q3 [obs-1: trend_analysis]",
                    observation_refs=["obs-1"]
                ),
                GroundedFinding(
                    finding="Enterprise customer segment generated 65% of overall sales [obs-2: group_by_analysis]",
                    observation_refs=["obs-2"]
                )
            ],
            recommendations=["Focus retention efforts on enterprise accounts."],
            limitations=["Observational data does not confirm causal mechanism."]
        )
    )

    agent = ReportGenerationAgent(llm_service=mock_llm)
    profile = {"dataset_name": "sales.csv", "row_count": 500, "col_count": 5}
    observations = [
        {"tool_name": "trend_analysis", "summary": "Quarterly drop of 24.5%", "output_data": {"drop": 24.5}},
        {"tool_name": "group_by_analysis", "summary": "Enterprise accounts 65%", "output_data": {"share": 65.0}}
    ]

    report = agent.generate_report(
        user_question="Why did sales drop?",
        profile=profile,
        observations=observations,
        charts=[],
        validation_result={},
        trace_logs=[],
        sources=["statistical_test_selection.md"]
    )

    assert report["title"] == "Analysis of Sales Contraction"
    assert len(report["key_findings"]) == 2
    assert "[obs-1: trend_analysis]" in report["key_findings"][0]
    assert report["sources"] == ["statistical_test_selection.md"]

def test_validation_layer1_deterministic_rejection():
    """Tests Layer 1 rejection of ungrounded or fabricated claims."""
    agent = ValidationAgent()
    observations = [
        {
            "tool_name": "trend_analysis",
            "summary": "Revenue dropped 24% in Q3",
            "output_data": {"pct_change": 24.0, "total": 1200.0},
            "success": True
        }
    ]

    report = {
        "key_findings": [
            # Valid claim: references obs-1 and number 24 exists in output
            "Revenue dropped 24% in Q3 [obs-1: trend_analysis]",
            # Fabricated claim: number 85 does NOT exist anywhere in observations
            "Customer dissatisfaction rose by 85% [obs-1: trend_analysis]",
            # Ungrounded claim: missing observation citation
            "Market competition increased significantly without citation."
        ]
    }

    val_res = agent.audit_report_claims(report, observations, "Analyze sales")

    # The fabricated number and ungrounded claim should be flagged as is_supported = False
    validations = val_res["validations"]
    unsupported = [v for v in validations if not v["is_supported"]]
    assert len(unsupported) >= 2

    # Report's key findings should only contain the verified claim
    assert len(report["key_findings"]) == 1
    assert "Revenue dropped 24%" in report["key_findings"][0]

def test_validation_layer2_llm_causal_verifier():
    """Tests Layer 2 LLM audit detecting causal language in correlational findings."""
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.invoke.return_value = LLMResponse(
        content="{\"overall_valid\": true}",
        parsed=LLMVerificationAudit(
            audits=[
                ClaimAuditItem(
                    claim="High discount rate drove customer churn [obs-1: correlation_analysis]",
                    verdict="overstated",
                    evidence="Correlation coefficient r=0.45 indicates association, not direct causation.",
                    causal_language_flag=True,
                    confidence_score=0.88,
                    suggested_caveat="Reflects linear correlation, not proven causation."
                )
            ],
            overall_valid=True,
            summary="Flagged causal claim on correlational data."
        )
    )

    agent = ValidationAgent(llm_service=mock_llm)
    observations = [
        {
            "tool_name": "correlation_analysis",
            "summary": "Discount rate and churn risk correlation r=0.45",
            "output_data": {"r": 0.45},
            "success": True
        }
    ]

    report = {
        "key_findings": [
            "High discount rate drove customer churn [obs-1: correlation_analysis]"
        ]
    }

    val_res = agent.audit_report_claims(report, observations, "What drove churn?")

    # Causal warning should be issued
    assert len(val_res["correlation_vs_causation_warnings"]) > 0
    # Finding should be amended with caveat note
    assert any("Observational Association" in f for f in report["key_findings"])
