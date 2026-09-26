from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    dataset_path: str
    user_question: str
    session_id: str
    profile: Optional[Dict[str, Any]]
    plan: Optional[Dict[str, Any]]
    current_step_idx: int
    observations: List[Dict[str, Any]]
    charts: List[Dict[str, Any]]
    requires_human_approval: bool
    approval_prompt: Optional[str]
    is_approved: bool
    validation_result: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]
    trace_logs: List[Dict[str, Any]]
    errors: List[str]
    completed: bool
