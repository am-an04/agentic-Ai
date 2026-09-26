from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ProfileSummary(BaseModel):
    dataset_name: str
    row_count: int
    col_count: int
    columns: List[str]
    dtypes: Dict[str, str]
    missing_counts: Dict[str, int]
    missing_percentages: Dict[str, float]
    duplicate_rows: int
    numerical_columns: List[str]
    categorical_columns: List[str]
    date_columns: List[str]
    potential_targets: List[str]
    outlier_counts: Dict[str, int]
    data_quality_score: float
    data_quality_issues: List[str]
    summary_stats: Dict[str, Any]

class PlanStep(BaseModel):
    step_number: int
    action: str
    description: str
    tool_needed: str
    status: str = "pending"  # pending, running, completed, failed

class AnalysisPlan(BaseModel):
    goal: str
    plan_steps: List[PlanStep]
    reasoning: str

class ToolExecutionResult(BaseModel):
    tool_name: str
    input_args: Dict[str, Any]
    output_data: Any
    summary: str
    success: bool
    execution_time_ms: float
    chart_json: Optional[Dict[str, Any]] = None

class ClaimValidation(BaseModel):
    claim: str
    is_supported: bool
    evidence: str
    confidence_score: float  # 0.0 to 1.0
    caveats: Optional[List[str]] = None

class ValidationResult(BaseModel):
    overall_valid: bool
    validations: List[ClaimValidation]
    correlation_vs_causation_warnings: List[str]
    sample_size_warnings: List[str]
    metric_warnings: List[str]
    summary: str

class AnalysisReport(BaseModel):
    title: str
    executive_summary: str
    dataset_overview: Dict[str, Any]
    key_findings: List[str]
    visual_insights: List[Dict[str, Any]]  # [{title, description, chart_spec}]
    statistical_findings: List[Dict[str, Any]]
    ml_results: Optional[Dict[str, Any]] = None
    recommendations: List[str]
    limitations: List[str]
    analysis_trace: List[Dict[str, Any]]
    created_at: str

class AnalyzeRequest(BaseModel):
    dataset_path: str
    user_question: str
    session_id: Optional[str] = None
    enable_ml: bool = True

class ApprovalRequest(BaseModel):
    session_id: str
    action_id: str
    approved: bool
