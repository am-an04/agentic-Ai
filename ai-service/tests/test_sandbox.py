import os
import pytest
import pandas as pd
from unittest.mock import MagicMock
from app.tools.sandbox import (
    validate_code_ast,
    execute_controlled_python,
    SandboxExecutionError
)
from app.agents.orchestrator import AgentOrchestrator
from app.core.llm import LLMService, LLMResponse

@pytest.fixture
def sample_csv(tmp_path):
    df = pd.DataFrame({
        "employee_id": [101, 102, 103, 104, 105],
        "department": ["Engineering", "Sales", "Engineering", "Marketing", "Sales"],
        "salary": [95000, 65000, 110000, 72000, 80000],
        "experience": [3, 2, 6, 4, 5]
    })
    path = str(tmp_path / "employees.csv")
    df.to_csv(path, index=False)
    return path

# 1. AST Validation Security Tests
def test_ast_prohibits_dangerous_imports():
    with pytest.raises(SandboxExecutionError, match="prohibited in sandbox"):
        validate_code_ast("import os\nresult = os.listdir('.')")

    with pytest.raises(SandboxExecutionError, match="prohibited in sandbox"):
        validate_code_ast("import subprocess\nresult = subprocess.run(['ls'])")

    with pytest.raises(SandboxExecutionError, match="prohibited in sandbox"):
        validate_code_ast("from pathlib import Path\nresult = Path('.').exists()")

def test_ast_prohibits_dangerous_calls_and_dunders():
    with pytest.raises(SandboxExecutionError, match="prohibited in sandbox"):
        validate_code_ast("f = open('test.txt', 'w')")

    with pytest.raises(SandboxExecutionError, match="prohibited in sandbox"):
        validate_code_ast("eval('1 + 1')")

    with pytest.raises(SandboxExecutionError, match="Special attribute"):
        validate_code_ast("result = [].__class__.__subclasses__()")

def test_ast_prohibits_file_writing_attributes():
    with pytest.raises(SandboxExecutionError, match="File write method 'to_csv' is blocked"):
        validate_code_ast("df.to_csv('leak.csv')")

    with pytest.raises(SandboxExecutionError, match="File write method 'to_excel' is blocked"):
        validate_code_ast("df.to_excel('leak.xlsx')")

def test_ast_allows_safe_data_analysis_modules():
    safe_code = """
import numpy as np
import math
import json
import re
result = df['salary'].mean()
"""
    # Should not raise
    validate_code_ast(safe_code)

# 2. Controlled Subprocess Execution Tests
def test_subprocess_executes_valid_pandas(sample_csv):
    code = "result = {'avg_salary': float(df['salary'].mean()), 'max_exp': int(df['experience'].max())}"
    res = execute_controlled_python(sample_csv, code)
    assert res["success"] is True
    assert res["result"]["avg_salary"] == 84400.0
    assert res["result"]["max_exp"] == 6
    assert "Result type: dict" in res["summary"]

def test_subprocess_handles_groupby_and_series(sample_csv):
    code = "result = df.groupby('department')['salary'].mean().to_dict()"
    res = execute_controlled_python(sample_csv, code)
    assert res["success"] is True
    assert isinstance(res["result"], dict)
    assert res["result"]["Engineering"] == 102500.0

def test_subprocess_blocks_malicious_code_at_ast(sample_csv):
    malicious_code = "import os\nresult = os.getcwd()"
    res = execute_controlled_python(sample_csv, malicious_code)
    assert res["success"] is False
    assert "Security violation" in res["error"]
    assert "Sandbox security rejection" in res["summary"]

def test_subprocess_execution_timeout(sample_csv):
    infinite_loop = "while True:\n    pass"
    res = execute_controlled_python(sample_csv, infinite_loop, timeout=1.0)
    assert res["success"] is False
    assert "limit exceeded" in res["error"]
    assert "CPU timeout" in res["summary"]

# 3. Orchestrator Integration & Self-Repair Retry Test
def test_orchestrator_analyst_code_self_repair(sample_csv):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.is_configured.return_value = True

    # When the first buggy snippet fails, LLM returns corrected code in markdown
    repaired_code = "result = float(df['salary'].mean())"
    mock_llm.invoke.return_value = LLMResponse(
        content=f"```python\n{repaired_code}\n```",
        prompt_tokens=50,
        completion_tokens=25,
        total_tokens=75,
        estimated_cost_usd=0.0001,
        latency_ms=120.0,
        provider="mock",
        model="mock-gpt"
    )

    orchestrator = AgentOrchestrator(llm_service=mock_llm)
    
    # Intentionally buggy initial code with unknown column
    trace_logs = []
    step_meta = {"action": "Compute Average Salary", "description": "Calculate mean salary"}
    params = {"code": "result = df['non_existent_column'].mean()", "purpose": "Calculate mean salary"}

    result = orchestrator._execute_analyst_code(
        file_path=sample_csv,
        params=params,
        step_meta=step_meta,
        trace_logs=trace_logs
    )

    assert result["success"] is True
    assert result["output_data"] == 84400.0
    assert "Self-repaired code succeeded" in result["summary"]
    assert any(log.get("step") == "Code Self-Repair Retry" for log in trace_logs)
