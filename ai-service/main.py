import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import AnalyzeRequest, ApprovalRequest
from app.agents.orchestrator import AgentOrchestrator
from app.tools.profiling_tools import profile_dataset
from app.tools.sandbox import execute_controlled_python

app = FastAPI(
    title="DataPilot AI Analysis Service",
    description="Autonomous Agentic AI Data Analyst Microservice powered by LangGraph, Pandas, SciPy, Scikit-learn, and Plotly.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import math
import numpy as np

def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return [sanitize_for_json(item) for item in obj.tolist()]
    elif isinstance(obj, (np.floating, float)):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    return obj

# In-memory session store for active agent states
SESSIONS = {}
orchestrator = AgentOrchestrator()

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "DataPilot AI Microservice"}

@app.post("/api/profile")
def profile_endpoint(request: dict):
    file_path = request.get("dataset_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="Valid 'dataset_path' is required.")
    try:
        return profile_dataset(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
def start_analysis(request: AnalyzeRequest):
    if not os.path.exists(request.dataset_path):
        raise HTTPException(status_code=400, detail=f"Dataset file not found at: {request.dataset_path}")
        
    session_id = request.session_id or f"session-{os.urandom(4).hex()}"
    
    initial_state = {
        "dataset_path": request.dataset_path,
        "user_question": request.user_question,
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
        "completed": False
    }

    final_state = orchestrator.run_analysis(initial_state)
    SESSIONS[session_id] = final_state
    
    return sanitize_for_json({
        "session_id": session_id,
        "completed": final_state["completed"],
        "requires_human_approval": final_state["requires_human_approval"],
        "approval_prompt": final_state.get("approval_prompt"),
        "plan": final_state.get("plan"),
        "observations_count": len(final_state.get("observations", [])),
        "charts_count": len(final_state.get("charts", [])),
        "validation_result": final_state.get("validation_result"),
        "final_report": final_state.get("final_report"),
        "trace_logs": final_state.get("trace_logs"),
        "sources": final_state.get("sources", [])
    })

@app.post("/api/approve")
def approve_action(request: ApprovalRequest):
    session_id = request.session_id
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Analysis session not found.")
        
    state = SESSIONS[session_id]
    if not state.get("requires_human_approval"):
        return {"message": "No pending approval required."}

    if request.approved:
        state["is_approved"] = True
        state["requires_human_approval"] = False
        state["trace_logs"].append({
            "step": "Human Approval Received",
            "description": "User granted approval. Resuming ML tool execution...",
            "timestamp": os.urandom(2).hex()
        })
        updated_state = orchestrator.run_analysis(state)
        SESSIONS[session_id] = updated_state
        return sanitize_for_json({
            "session_id": session_id,
            "completed": updated_state["completed"],
            "final_report": updated_state.get("final_report"),
            "trace_logs": updated_state.get("trace_logs"),
            "sources": updated_state.get("sources", [])
        })
    else:
        state["requires_human_approval"] = False
        state["trace_logs"].append({
            "step": "Human Approval Denied",
            "description": "User skipped ML training. Proceeding directly to report synthesis...",
            "timestamp": os.urandom(2).hex()
        })
        # Skip ML and finalize
        r_res = orchestrator.report_agent.generate_report(
            user_question=state["user_question"],
            profile=state["profile"],
            observations=state["observations"],
            charts=state["charts"],
            validation_result=state.get("validation_result", {}),
            trace_logs=state["trace_logs"],
            sources=state.get("sources", [])
        )
        state["final_report"] = r_res
        state["completed"] = True
        SESSIONS[session_id] = state
        return sanitize_for_json({
            "session_id": session_id,
            "completed": True,
            "final_report": r_res,
            "trace_logs": state.get("trace_logs"),
            "sources": state.get("sources", [])
        })

from app.core.knowledge import get_knowledge_store

@app.post("/api/dataset/{dataset_id}/dictionary")
def set_dataset_dictionary(dataset_id: str, request: dict):
    definitions = request.get("definitions", {})
    get_knowledge_store().set_data_dictionary(dataset_id, definitions)
    return {"message": "Data dictionary saved.", "dataset_id": dataset_id, "definitions": definitions}

@app.get("/api/dataset/{dataset_id}/dictionary")
def get_dataset_dictionary(dataset_id: str):
    defs = get_knowledge_store().get_data_dictionary(dataset_id)
    return {"dataset_id": dataset_id, "definitions": defs}

@app.post("/api/sandbox")
def sandbox_endpoint(request: dict):
    file_path = request.get("dataset_path")
    code_snippet = request.get("code")
    if not file_path or not code_snippet:
        raise HTTPException(status_code=400, detail="'dataset_path' and 'code' are required.")
    return execute_controlled_python(file_path, code_snippet)
@app.delete("/api/session/{session_id}")
def delete_session(session_id: str):
    if session_id in SESSIONS:
        del SESSIONS[session_id]
    return {"message": "Session cleaned up.", "session_id": session_id}

@app.delete("/api/sessions")
def delete_all_sessions():
    SESSIONS.clear()
    return {"message": "All sessions cleared."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
