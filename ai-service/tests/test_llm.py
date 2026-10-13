import pytest
import json
from unittest.mock import MagicMock, patch
from pydantic import BaseModel, Field
from app.core.llm import (
    LLMService,
    LLMResponse,
    LLMMessage,
    _clean_json_markdown,
    calculate_cost,
    get_llm_service,
)

class SamplePlanStep(BaseModel):
    step_number: int
    action: str
    description: str

class SamplePlan(BaseModel):
    goal: str
    steps: list[SamplePlanStep]
    reasoning: str

def test_clean_json_markdown():
    # Markdown with json tag
    wrapped = "```json\n{\"key\": \"value\"}\n```"
    assert _clean_json_markdown(wrapped) == '{"key": "value"}'

    # Markdown without language tag
    wrapped_bare = "```\n{\"key\": \"value\"}\n```"
    assert _clean_json_markdown(wrapped_bare) == '{"key": "value"}'

    # Raw JSON
    raw = '{"key": "value"}'
    assert _clean_json_markdown(raw) == '{"key": "value"}'

def test_calculate_cost():
    # GPT-4o: $2.50 per 1M prompt, $10.00 per 1M completion
    cost_gpt4o = calculate_cost(1000, 500, "gpt-4o")
    expected = (1000 * 2.50 + 500 * 10.00) / 1_000_000.0
    assert pytest.approx(cost_gpt4o, 1e-6) == expected

    # Gemini 2.5 Flash: $0.075 per 1M prompt, $0.30 per 1M completion
    cost_gemini = calculate_cost(10000, 2000, "gemini-2.5-flash")
    expected_gemini = (10000 * 0.075 + 2000 * 0.30) / 1_000_000.0
    assert pytest.approx(cost_gemini, 1e-6) == expected_gemini

    # Ollama: 0.0
    cost_ollama = calculate_cost(5000, 5000, "ollama")
    assert cost_ollama == 0.0

def test_to_trace_log_format():
    resp = LLMResponse(
        content="{\"test\": 123}",
        parsed={"test": 123},
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        estimated_cost_usd=0.0005,
        latency_ms=120.5,
        provider="openai",
        model="gpt-4o",
        validation_retries=1
    )
    trace = resp.to_trace_log("Planner Reasoning")
    assert trace["step"] == "Planner Reasoning"
    assert "LLM [openai:gpt-4o]" in trace["description"]
    assert "Self-repaired after 1 retries" in trace["description"]
    assert "llm_usage" in trace
    assert trace["llm_usage"]["total_tokens"] == 150
    assert trace["llm_usage"]["estimated_cost_usd"] == 0.0005

def test_structured_output_success():
    service = LLMService(provider="openai", model="gpt-4o", api_key="fake-key")
    valid_json = json.dumps({
        "goal": "Analyze churn drivers",
        "steps": [
            {"step_number": 1, "action": "Profile", "description": "Profile dataset"}
        ],
        "reasoning": "Standard EDA flow"
    })

    with patch.object(service, "_call_raw_provider", return_value=(f"```json\n{valid_json}\n```", 100, 50)):
        result = service.invoke("Analyze churn", response_schema=SamplePlan)
        assert result.parsed is not None
        assert isinstance(result.parsed, SamplePlan)
        assert result.parsed.goal == "Analyze churn drivers"
        assert len(result.parsed.steps) == 1
        assert result.validation_retries == 0
        assert result.total_tokens == 150

def test_structured_output_self_repair_retry():
    """Tests that a malformed JSON on attempt 1 triggers feedback and repairs on attempt 2."""
    service = LLMService(provider="gemini", model="gemini-2.5-flash", api_key="fake-key", max_validation_retries=2)
    
    invalid_json = '{"goal": "Incomplete json", "steps": '  # syntax error
    valid_json = json.dumps({
        "goal": "Repaired churn plan",
        "steps": [
            {"step_number": 1, "action": "Inspect", "description": "Inspect missing values"}
        ],
        "reasoning": "Corrected JSON"
    })

    # Call 1 returns invalid, Call 2 returns valid
    mock_calls = [
        (invalid_json, 80, 20),
        (valid_json, 120, 45)
    ]

    with patch.object(service, "_call_raw_provider", side_effect=mock_calls) as mock_raw:
        result = service.invoke("Analyze churn", response_schema=SamplePlan)
        assert mock_raw.call_count == 2
        assert result.parsed is not None
        assert result.parsed.goal == "Repaired churn plan"
        assert result.validation_retries == 1
        assert result.total_tokens == (80 + 20) + (120 + 45)

def test_structured_output_exhausts_retries():
    """Tests that continuing to fail exhausts retries and raises a ValueError."""
    service = LLMService(provider="openai", model="gpt-4o", api_key="fake-key", max_validation_retries=2)
    invalid_json = '{"invalid": true}'

    with patch.object(service, "_call_raw_provider", return_value=(invalid_json, 50, 10)):
        with pytest.raises(ValueError, match="Failed to produce valid output"):
            service.invoke("Analyze churn", response_schema=SamplePlan)

def test_missing_api_keys_raise_error():
    empty_env = {"OPENAI_API_KEY": "", "ANTHROPIC_API_KEY": "", "GEMINI_API_KEY": ""}
    # OpenAI missing key
    with patch.dict("os.environ", empty_env):
        service = LLMService(provider="openai", api_key=None)
        with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
            service._call_openai([{"role": "user", "content": "hi"}])

    # Anthropic missing key
    with patch.dict("os.environ", empty_env):
        service = LLMService(provider="anthropic", api_key=None)
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is not set"):
            service._call_anthropic([{"role": "user", "content": "hi"}])

    # Gemini missing key
    with patch.dict("os.environ", empty_env):
        service = LLMService(provider="gemini", api_key=None)
        with pytest.raises(ValueError, match="GEMINI_API_KEY is not set"):
            service._call_gemini([{"role": "user", "content": "hi"}])

def test_unsupported_provider():
    service = LLMService(provider="unknown_provider")
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        service.invoke("Hello")

def test_streaming_mock():
    service = LLMService(provider="openai", api_key="fake-key")

    mock_chunk1 = MagicMock()
    mock_chunk1.choices = [MagicMock(delta=MagicMock(content="Hello "))]
    mock_chunk2 = MagicMock()
    mock_chunk2.choices = [MagicMock(delta=MagicMock(content="World!"))]

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = [mock_chunk1, mock_chunk2]

        chunks = list(service.stream("Greet the world"))
        assert "".join(chunks) == "Hello World!"
