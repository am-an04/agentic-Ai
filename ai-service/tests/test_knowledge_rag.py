import os
import pytest
from app.core.knowledge import (
    KnowledgeStore,
    chunk_markdown_text,
    retrieve,
    retrieve_guidance_for_query,
    get_methodology_guidance,
    get_knowledge_store
)

def test_chunk_markdown_text():
    sample_doc = (
        "# Statistical Guidelines\n\n"
        "Use independent t-test when comparing continuous variables across two groups.\n\n"
        "## One-Way ANOVA\n\n"
        "Use ANOVA when comparing 3 or more categorical groups."
    )
    chunks = chunk_markdown_text(sample_doc, source_name="statistical_test_selection.md")
    assert len(chunks) >= 2
    assert chunks[0].source == "statistical_test_selection.md"
    assert chunks[0].topic == "statistics"
    assert "t-test" in chunks[0].text or "ANOVA" in chunks[1].text

def test_knowledge_docs_indexed_and_retrieved():
    store = get_knowledge_store()
    assert store is not None

    # Retrieve statistical guidance
    stat_chunks = store.retrieve("p-value threshold and t-test sample size", k=2)
    assert len(stat_chunks) > 0
    sources = [c.source for c in stat_chunks]
    assert any("statistical" in s.lower() for s in sources)

    # Retrieve ML guidance
    ml_chunks = store.retrieve("R2 score regression and holdout test set", k=2)
    assert len(ml_chunks) > 0
    ml_sources = [c.source for c in ml_chunks]
    assert any("ml" in s.lower() for s in ml_sources)

    # Retrieve Viz guidance
    viz_chunks = store.retrieve("line chart for time series and quarterly trends", k=2)
    assert len(viz_chunks) > 0
    viz_sources = [c.source for c in viz_chunks]
    assert any("visualization" in s.lower() for s in viz_sources)

def test_retrieve_guidance_for_query():
    guidance, sources = retrieve_guidance_for_query("How should I evaluate classification models?", k=3)
    assert len(sources) > 0
    assert len(guidance) > 0
    assert any("ml_evaluation" in s for s in sources)
    # Source citation header in text
    assert "[" in guidance and "]" in guidance

def test_data_dictionary_storage_and_retrieval():
    store = get_knowledge_store()
    dataset_id = "ds_customer_123"
    definitions = {
        "churn_risk": "Binary indicator: 1 if customer cancelled contract within 30 days, else 0.",
        "monthly_charges": "Recurring billing amount in USD charged on the first of each month."
    }

    store.set_data_dictionary(dataset_id, definitions)
    retrieved_dict = store.get_data_dictionary(dataset_id)

    assert retrieved_dict["churn_risk"] == definitions["churn_risk"]
    assert retrieved_dict["monthly_charges"] == definitions["monthly_charges"]

def test_index_and_retrieve_past_sessions():
    store = get_knowledge_store()
    session_id = "sess_q3_sales"
    user_q = "Why did Q3 sales revenue decline?"
    report = {
        "executive_summary": "Q3 revenue dropped 24% primarily in West region clothing line.",
        "key_findings": ["Significant 24% period drop in Q3", "West region underperformed East by 40%"]
    }

    store.index_past_session(session_id, user_q, report)
    chunks = store.retrieve("Q3 revenue West region decline", k=1, collection_name="past_sessions")

    assert len(chunks) > 0
    assert "sess_q3_sales" in chunks[0].chunk_id
    assert "24%" in chunks[0].text

def test_backward_compatible_guidance():
    guidance = get_methodology_guidance("statistical_guidelines")
    assert "p_value_threshold" in guidance
    assert "0.05" in guidance
