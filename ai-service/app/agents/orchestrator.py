import time
import os
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.state import AgentState
from app.agents.profiling_agent import DataProfilingAgent
from app.agents.eda_agent import EDAAgent
from app.agents.stats_agent import StatisticsAgent
from app.agents.ml_agent import MLAgent
from app.agents.viz_agent import VisualizationAgent
from app.agents.validation_agent import ValidationAgent
from app.agents.report_agent import ReportGenerationAgent
from app.agents.planner import LLMPlanner, sanitize_and_repair_plan
from app.tools.catalog import TOOL_CATALOG, resolve_tool_name
from app.tools.sandbox import execute_controlled_python
from app.core.llm import LLMService, LLMMessage, get_llm_service
from app.core.knowledge import retrieve_guidance_for_query, get_knowledge_store

class ReflectionDecision(BaseModel):
    decision: str = Field(description="'continue' | 'add_step' | 'conclude'")
    reasoning: str = Field(description="Brief analytical justification for the decision")
    action: Optional[str] = Field(default=None, description="Action title if add_step")
    description: Optional[str] = Field(default=None, description="Step description if add_step")
    tool_needed: Optional[str] = Field(default=None, description="Tool from TOOL_CATALOG if add_step")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Tool parameters if add_step")

class AgentOrchestrator:
    def __init__(self, planner: Optional[LLMPlanner] = None, llm_service: Optional[LLMService] = None):
        self.profiler = DataProfilingAgent()
        self.eda_agent = EDAAgent()
        self.stats_agent = StatisticsAgent()
        self.ml_agent = MLAgent()
        self.viz_agent = VisualizationAgent()
        self.validation_agent = ValidationAgent()
        self.report_agent = ReportGenerationAgent()
        self.planner = planner or LLMPlanner()
        self.llm_service = llm_service or get_llm_service()
        self.checkpointer = MemorySaver()
        self.graph = self._build_state_graph().compile(checkpointer=self.checkpointer)

    def _build_state_graph(self) -> StateGraph:
        """Constructs the LangGraph StateGraph representing the autonomous agent pipeline."""
        workflow = StateGraph(AgentState)

        # 1. Add nodes
        workflow.add_node("profile", self._node_profile)
        workflow.add_node("plan", self._node_plan)
        workflow.add_node("execute_step", self._node_execute_step)
        workflow.add_node("reflect", self._node_reflect)
        workflow.add_node("validate", self._node_validate)
        workflow.add_node("report", self._node_report)

        # 2. Add fixed edges
        workflow.set_entry_point("profile")
        workflow.add_edge("profile", "plan")
        workflow.add_edge("plan", "execute_step")

        # 3. Conditional edge after step execution (handles human approval pause)
        workflow.add_conditional_edges(
            "execute_step",
            self._route_after_execute,
            {
                "pause_approval": END,
                "reflect": "reflect",
                "validate": "validate"
            }
        )

        # 4. Conditional edge after reflection (loop, continue, or validate)
        workflow.add_conditional_edges(
            "reflect",
            self._route_after_reflect,
            {
                "execute_step": "execute_step",
                "validate": "validate"
            }
        )

        workflow.add_edge("validate", "report")
        workflow.add_edge("report", END)

        return workflow

    # =========================================================================
    # Node implementations
    # =========================================================================

    def _node_profile(self, state: AgentState) -> Dict[str, Any]:
        """Profiles the dataset if not already done."""
        if state.get("profile"):
            return {}

        file_path = state["dataset_path"]
        trace = {
            "step": "Understand & Profile",
            "description": "Inspecting dataset shape, schema, dtypes, and quality score...",
            "timestamp": time.time()
        }
        prof_res = self.profiler.execute(file_path)
        profile_data = prof_res["profile_data"]
        trace["description"] += f" Found {profile_data.get('row_count')} rows, {profile_data.get('col_count')} columns."

        trace_logs = list(state.get("trace_logs", []))
        trace_logs.append(trace)

        return {
            "profile": profile_data,
            "trace_logs": trace_logs
        }

    def _node_plan(self, state: AgentState) -> Dict[str, Any]:
        """Formulates the analysis plan via LLMPlanner (with rule-based fallback)."""
        if state.get("plan"):
            return {}

        question = state["user_question"]
        profile = state.get("profile", {})
        enable_ml = state.get("enable_ml", True)
        trace_logs = list(state.get("trace_logs", []))

        trace_logs.append({
            "step": "Create Plan",
            "description": f"Formulating analytical workflow for: '{question}'",
            "timestamp": time.time()
        })

        # Retrieve methodology guidance via RAG
        guidance, sources = retrieve_guidance_for_query(question, k=4)
        state_sources = list(state.get("sources", []))
        for s in sources:
            if s not in state_sources:
                state_sources.append(s)

        if sources:
            trace_logs.append({
                "step": "Retrieve Methodology Guidance",
                "description": f"Retrieved {len(sources)} guidance documents: {', '.join(sources)}",
                "timestamp": time.time(),
                "sources": sources
            })

        plan = self.create_plan(
            question=question,
            profile=profile,
            enable_ml=enable_ml,
            trace_logs=trace_logs,
            retrieved_guidance=guidance or state.get("retrieved_guidance")
        )

        return {
            "plan": plan,
            "current_step_idx": 0,
            "trace_logs": trace_logs,
            "sources": state_sources,
            "retrieved_guidance": guidance
        }

    def _node_execute_step(self, state: AgentState) -> Dict[str, Any]:
        """Executes the next pending step from the plan."""
        plan = state.get("plan", {})
        steps = plan.get("plan_steps", [])
        file_path = state["dataset_path"]
        trace_logs = list(state.get("trace_logs", []))
        observations = list(state.get("observations", []))
        charts = list(state.get("charts", []))

        # Find the next pending step (skipping profile, validate, report)
        target_step = None
        for step in steps:
            if step["status"] == "pending" and step.get("tool_needed") not in ["profile_dataset", "validate_claims", "generate_report"]:
                target_step = step
                break

        if not target_step:
            return {}

        tool_name = target_step.get("tool_needed")
        params = target_step.get("params", {})

        # Check for Human-in-the-Loop approval
        if target_step.get("requires_approval") and not state.get("is_approved", False):
            approval_prompt = (
                f"Action '{target_step['action']}' ({tool_name}) requires confirmation. "
                f"Proceed with Machine Learning training?"
            )
            trace_logs.append({
                "step": "Human Approval Required",
                "description": approval_prompt,
                "timestamp": time.time()
            })
            return {
                "requires_human_approval": True,
                "approval_prompt": approval_prompt,
                "trace_logs": trace_logs
            }

        trace_logs.append({
            "step": f"Executing Tool: {tool_name}",
            "description": target_step.get("description", f"Running {tool_name}"),
            "timestamp": time.time()
        })

        # Route tool execution
        res = None
        canon_tool = resolve_tool_name(tool_name)
        if canon_tool in ["correlation_analysis", "group_by_analysis", "trend_analysis", "distribution_analysis"]:
            res = self.eda_agent.execute_tool(canon_tool, file_path, params)
        elif canon_tool in ["ttest", "chi_square", "anova"]:
            res = self.stats_agent.execute_tool(canon_tool, file_path, params)
        elif canon_tool in ["train_regression", "train_classification", "train_clustering"]:
            res = self.ml_agent.execute_tool(canon_tool, file_path, params)
        elif canon_tool in ["bar_chart", "line_chart", "scatter_plot", "box_plot", "heatmap"]:
            res = self.viz_agent.execute_tool(canon_tool, file_path, params)
            if res.get("success"):
                charts.append(res)
        elif canon_tool == "analyst_code":
            res = self._execute_analyst_code(file_path, params, target_step, trace_logs)

        if res:
            target_step["status"] = "completed" if res.get("success") else "failed"
            observations.append(res)
        else:
            target_step["status"] = "failed"

        return {
            "observations": observations,
            "charts": charts,
            "trace_logs": trace_logs,
            "plan": plan
        }

    def _execute_analyst_code(
        self,
        file_path: str,
        params: Dict[str, Any],
        step_meta: Dict[str, Any],
        trace_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Executes model-generated Python code in the secure subprocess sandbox.
        If execution fails (e.g. KeyError, syntax error, or sandbox rejection), performs
        a 1-turn self-repair retry loop with the LLM before returning.
        """
        code = params.get("code", "")
        purpose = params.get("purpose") or step_meta.get("description", "Execute custom calculation")

        # If no code was provided in params, ask LLM to generate it
        if not code.strip() and self.llm_service and self.llm_service.is_configured():
            prompt = (
                f"You are an expert Python data analyst. Write a concise Pandas snippet to achieve: {purpose}\n"
                f"The dataset is already loaded as DataFrame `df`.\n"
                f"Assign the final computation (scalar, dict, series, or dataframe) to variable `result`.\n"
                f"Allowed modules: pandas (as pd), numpy (as np), math, scipy, datetime, json, re.\n"
                f"Security constraints: Do NOT write files, do NOT call eval/exec/open, do NOT import os/sys.\n"
                f"Return ONLY python code inside ```python ... ```."
            )
            try:
                gen_res = self.llm_service.invoke([
                    LLMMessage(role="system", content="You are a data analysis code generator. Write safe pandas code."),
                    LLMMessage(role="user", content=prompt)
                ])
                trace_logs.append(gen_res.to_trace_log("Code Generation"))
                match = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", gen_res.content)
                code = match.group(1).strip() if match else gen_res.content.strip()
            except Exception as e:
                code = ""

        # First execution attempt
        exec_res = execute_controlled_python(file_path, code)

        # If failed and LLM is configured, attempt 1 self-repair turn
        if not exec_res.get("success") and self.llm_service and self.llm_service.is_configured() and code.strip():
            error_reason = exec_res.get("error") or exec_res.get("summary")
            repair_prompt = (
                f"The following Python code snippet failed in our sandbox against DataFrame `df`:\n"
                f"```python\n{code}\n```\n"
                f"Sandbox error encountered: {error_reason}\n\n"
                f"Goal: {purpose}\n"
                f"Please fix the code. Ensure:\n"
                f"1. Final answer is assigned to `result`.\n"
                f"2. Allowed modules: pandas (as pd), numpy (as np), math, scipy, datetime, json, re.\n"
                f"3. No open(), eval(), exec(), or file writing (to_csv, etc.).\n"
                f"Return ONLY the corrected python code in ```python ... ```."
            )
            try:
                repair_llm = self.llm_service.invoke([
                    LLMMessage(role="system", content="You repair failed data analysis code snippets."),
                    LLMMessage(role="user", content=repair_prompt)
                ])
                trace_logs.append(repair_llm.to_trace_log("Code Self-Repair Retry"))
                match = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", repair_llm.content)
                repaired_code = match.group(1).strip() if match else repair_llm.content.strip()

                retry_res = execute_controlled_python(file_path, repaired_code)
                if retry_res.get("success"):
                    exec_res = retry_res
                    exec_res["summary"] = f"Self-repaired code succeeded. {exec_res.get('summary', '')}"
                else:
                    exec_res = retry_res
            except Exception as e:
                trace_logs.append({
                    "step": "Code Self-Repair Error",
                    "description": f"Failed self-repair attempt: {str(e)}",
                    "timestamp": time.time()
                })

        return {
            "tool_name": "analyst_code",
            "output_data": exec_res.get("result"),
            "summary": exec_res.get("summary", "Custom Python execution completed."),
            "success": exec_res.get("success", False),
            "error": exec_res.get("error")
        }

    def _node_reflect(self, state: AgentState) -> Dict[str, Any]:
        """
        Reflection Node: The LLM analyzes the latest observation and determines whether to:
        1. 'continue' with the existing plan
        2. 'add_step' to drill into an unexpected anomaly or segment
        3. 'conclude' early because the question is sufficiently answered.
        Enforces a maximum step budget (default 12) to prevent infinite loops.
        """
        observations = state.get("observations", [])
        if not observations:
            return {}

        max_budget = state.get("step_budget") or 12
        plan = state.get("plan", {})
        steps = plan.get("plan_steps", [])
        trace_logs = list(state.get("trace_logs", []))
        reflection_notes = list(state.get("reflection_notes", []))

        # Enforce budget constraint
        if len(observations) >= max_budget:
            trace_logs.append({
                "step": "Step Budget Limit Reached",
                "description": f"Reached maximum observation budget ({max_budget} tool steps). Proceeding to claim validation.",
                "timestamp": time.time()
            })
            # Mark all pending intermediate steps as skipped
            for s in steps:
                if s["status"] == "pending" and s.get("tool_needed") not in ["validate_claims", "generate_report"]:
                    s["status"] = "skipped"
            return {
                "trace_logs": trace_logs,
                "plan": plan
            }

        latest_obs = observations[-1]
        user_question = state.get("user_question", "")
        profile = state.get("profile", {})

        # Ask LLM to evaluate the latest observation
        prompt = (
            f"You are the DataPilot Reflection Agent.\n"
            f"User Question: '{user_question}'\n"
            f"Latest Tool Executed: '{latest_obs.get('tool_name')}'\n"
            f"Observation Summary: {latest_obs.get('summary')}\n"
            f"Key Output Metrics: {str(latest_obs.get('output_data'))[:400]}\n"
            f"Observations Collected So Far: {len(observations)} (Max Budget: {max_budget})\n\n"
            f"Decide the next action:\n"
            f"- 'continue': proceed with existing planned steps\n"
            f"- 'add_step': add an immediate follow-up step to investigate an anomaly or subgroup\n"
            f"- 'conclude': analytical question has been sufficiently answered; skip remaining intermediate steps\n"
        )

        try:
            llm_resp = self.llm_service.invoke(
                messages=[{"role": "user", "content": prompt}],
                response_schema=ReflectionDecision
            )
            decision: ReflectionDecision = llm_resp.parsed

            reflection_notes.append({
                "step_idx": len(observations),
                "decision": decision.decision,
                "reasoning": decision.reasoning
            })

            if decision.decision == "add_step" and decision.tool_needed:
                tool_canon = resolve_tool_name(decision.tool_needed)
                if tool_canon in TOOL_CATALOG and len(observations) + 1 < max_budget:
                    # Find insertion index right before validate_claims
                    insert_idx = len(steps) - 1
                    for idx, s in enumerate(steps):
                        if s.get("tool_needed") == "validate_claims":
                            insert_idx = idx
                            break

                    new_step = {
                        "step_number": insert_idx + 1,
                        "action": decision.action or f"Follow-up: {tool_canon}",
                        "description": decision.description or decision.reasoning,
                        "tool_needed": tool_canon,
                        "params": decision.params or {},
                        "status": "pending",
                        "requires_approval": TOOL_CATALOG[tool_canon]["category"] == "ml"
                    }
                    steps.insert(insert_idx, new_step)

                    # Re-number steps
                    for i, s in enumerate(steps, start=1):
                        s["step_number"] = i

                    trace_logs.append({
                        "step": "Reflect: Adaptive Step Added",
                        "description": f"Reflect node added follow-up step: '{new_step['action']}'. Reasoning: {decision.reasoning}",
                        "timestamp": time.time()
                    })

            elif decision.decision == "conclude":
                trace_logs.append({
                    "step": "Reflect: Conclude Early",
                    "description": f"Reflect node concluded analysis early: Question answered. Reasoning: {decision.reasoning}",
                    "timestamp": time.time()
                })
                # Skip pending intermediate steps
                for s in steps:
                    if s["status"] == "pending" and s.get("tool_needed") not in ["validate_claims", "generate_report"]:
                        s["status"] = "skipped"

        except Exception as e:
            # Reflection failure fallback: silently continue without interrupting the pipeline
            reflection_notes.append({"decision": "continue", "error": str(e)})

        return {
            "trace_logs": trace_logs,
            "plan": plan,
            "reflection_notes": reflection_notes
        }

    def _node_validate(self, state: AgentState) -> Dict[str, Any]:
        """Validates observations, claims, and causal language."""
        trace_logs = list(state.get("trace_logs", []))
        trace_logs.append({
            "step": "Validate Findings",
            "description": "Auditing empirical observations and correlation-vs-causation validity...",
            "timestamp": time.time()
        })
        v_res = self.validation_agent.validate(state.get("observations", []), state["user_question"])

        plan = state.get("plan", {})
        for s in plan.get("plan_steps", []):
            if s.get("tool_needed") == "validate_claims":
                s["status"] = "completed"

        return {
            "validation_result": v_res,
            "trace_logs": trace_logs,
            "plan": plan
        }

    def _node_report(self, state: AgentState) -> Dict[str, Any]:
        """Synthesizes final structured executive analysis report."""
        trace_logs = list(state.get("trace_logs", []))
        trace_logs.append({
            "step": "Generate Report",
            "description": "Synthesizing executive summary, key findings, and recommendations...",
            "timestamp": time.time()
        })

        sources = state.get("sources", [])
        r_res = self.report_agent.generate_report(
            user_question=state["user_question"],
            profile=state.get("profile", {}),
            observations=state.get("observations", []),
            charts=state.get("charts", []),
            validation_result=state.get("validation_result", {}),
            trace_logs=trace_logs,
            sources=sources,
            retrieved_guidance=state.get("retrieved_guidance")
        )

        # Run Two-Layer Verification Audit on the synthesized report claims
        v_res = self.validation_agent.audit_report_claims(
            report=r_res,
            observations=state.get("observations", []),
            user_question=state["user_question"]
        )

        trace_logs.append({
            "step": "Two-Layer Claim Audit",
            "description": v_res.get("summary", "Claims audited."),
            "timestamp": time.time()
        })

        # Index past session summary for future cross-session retrieval
        try:
            get_knowledge_store().index_past_session(
                session_id=state.get("session_id", "sess"),
                user_question=state["user_question"],
                final_report=r_res
            )
        except Exception:
            pass

        plan = state.get("plan", {})
        for s in plan.get("plan_steps", []):
            if s.get("tool_needed") == "generate_report":
                s["status"] = "completed"

        return {
            "final_report": r_res,
            "validation_result": v_res,
            "completed": True,
            "trace_logs": trace_logs,
            "sources": sources,
            "plan": plan
        }

    # =========================================================================
    # Conditional edge routing
    # =========================================================================

    def _route_after_execute(self, state: AgentState) -> str:
        """Determines routing immediately after a step executes."""
        if state.get("requires_human_approval"):
            return "pause_approval"
        return "reflect"

    def _route_after_reflect(self, state: AgentState) -> str:
        """Determines whether to loop to another step or proceed to validation."""
        steps = state.get("plan", {}).get("plan_steps", [])
        has_pending = any(
            s["status"] == "pending" and s.get("tool_needed") not in ["profile_dataset", "validate_claims", "generate_report"]
            for s in steps
        )
        if has_pending:
            return "execute_step"
        return "validate"

    # =========================================================================
    # Public execution entrypoint
    # =========================================================================

    def create_plan(
        self,
        question: str,
        profile: Dict[str, Any],
        enable_ml: bool = True,
        trace_logs: Optional[List[Dict[str, Any]]] = None,
        retrieved_guidance: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates an analytical plan by calling the LLM planner first, falling back to rule-based on failure."""
        try:
            plan, trace_entry = self.planner.generate_plan(
                question=question,
                profile=profile,
                enable_ml=enable_ml,
                retrieved_guidance=retrieved_guidance
            )
            if trace_logs is not None:
                trace_logs.append(trace_entry)
            return plan
        except Exception as e:
            if trace_logs is not None:
                trace_logs.append({
                    "step": "Planner Fallback",
                    "description": f"LLM Planner unavailable or failed ({str(e)}). Falling back to deterministic rule-based planner.",
                    "timestamp": time.time()
                })
            return self._create_rule_based_plan(question, profile, enable_ml=enable_ml)

    def _create_rule_based_plan(self, question: str, profile: Dict[str, Any], enable_ml: bool = True) -> Dict[str, Any]:
        """Fallback rule-based analytical planner using keyword heuristics."""
        q_lower = question.lower()
        cols = profile.get("columns", [])
        num_cols = profile.get("numerical_columns", [])
        cat_cols = profile.get("categorical_columns", [])
        date_cols = profile.get("date_columns", [])

        steps = []
        step_num = 1

        # Profiling
        steps.append({
            "step_number": step_num,
            "action": "Profile Dataset",
            "description": f"Inspected dataset shape ({profile.get('row_count')} rows x {profile.get('col_count')} cols) and data quality.",
            "tool_needed": "profile_dataset",
            "params": {},
            "status": "completed",
            "requires_approval": False
        })
        step_num += 1

        if any(kw in q_lower for kw in ["sales", "revenue", "q3", "decrease", "decline", "trend", "fall"]):
            date_col = date_cols[0] if date_cols else (cols[1] if len(cols) > 1 else "order_date")
            val_col = "revenue" if "revenue" in cols else (num_cols[0] if num_cols else "sales")
            cat_col = cat_cols[0] if cat_cols else "region"

            steps.append({
                "step_number": step_num,
                "action": "Analyze Quarterly Trend",
                "description": f"Calculate quarterly trend for '{val_col}' over '{date_col}'.",
                "tool_needed": "trend_analysis",
                "params": {"date_col": date_col, "value_col": val_col, "freq": "Q"},
                "status": "pending",
                "requires_approval": False
            })
            step_num += 1

            if len(cat_cols) > 0:
                steps.append({
                    "step_number": step_num,
                    "action": "Investigate Categorical Performance",
                    "description": f"Group '{val_col}' by '{cat_col}'.",
                    "tool_needed": "group_by_analysis",
                    "params": {"group_col": cat_col, "target_col": val_col, "agg_funcs": ["sum", "mean", "count"]},
                    "status": "pending",
                    "requires_approval": False
                })
                step_num += 1

            if len(num_cols) >= 2:
                steps.append({
                    "step_number": step_num,
                    "action": "Correlation Analysis on Factors",
                    "description": f"Compute correlations between '{val_col}' and numeric factors.",
                    "tool_needed": "correlation_analysis",
                    "params": {"columns": num_cols},
                    "status": "pending",
                    "requires_approval": False
                })
                step_num += 1

            steps.append({
                "step_number": step_num,
                "action": "Generate Quarterly Trend Chart",
                "description": f"Plot interactive line chart of '{val_col}'.",
                "tool_needed": "line_chart",
                "params": {"x_col": date_col, "y_col": val_col, "title": "Quarterly Revenue Trend"},
                "status": "pending",
                "requires_approval": False
            })
            step_num += 1

        elif any(kw in q_lower for kw in ["churn", "factor", "associate", "predict", "driver"]):
            target = "churn_risk" if "churn_risk" in cols else (num_cols[0] if num_cols else cols[-1])

            steps.append({
                "step_number": step_num,
                "action": "Analyze Feature Correlations",
                "description": f"Compute correlation matrix against target variable '{target}'.",
                "tool_needed": "correlation_analysis",
                "params": {"columns": num_cols},
                "status": "pending",
                "requires_approval": False
            })
            step_num += 1

            if enable_ml:
                steps.append({
                    "step_number": step_num,
                    "action": "Train Machine Learning Model",
                    "description": f"Train Random Forest Classifier to identify top churn drivers.",
                    "tool_needed": "train_classification",
                    "params": {"target_col": target, "model_type": "random_forest"},
                    "requires_approval": True,
                    "status": "pending"
                })
                step_num += 1

            steps.append({
                "step_number": step_num,
                "action": "Generate Heatmap Chart",
                "description": "Generate correlation heatmap visualization.",
                "tool_needed": "heatmap",
                "params": {"title": "Correlation Matrix of Risk Drivers"},
                "status": "pending",
                "requires_approval": False
            })
            step_num += 1

        else:
            if len(num_cols) > 0:
                steps.append({
                    "step_number": step_num,
                    "action": "Distribution Analysis",
                    "description": f"Analyze distribution of metric '{num_cols[0]}'.",
                    "tool_needed": "distribution_analysis",
                    "params": {"column": num_cols[0]},
                    "status": "pending",
                    "requires_approval": False
                })
                step_num += 1

            if len(num_cols) >= 2:
                steps.append({
                    "step_number": step_num,
                    "action": "Correlation Matrix",
                    "description": "Calculate correlation matrix for numerical variables.",
                    "tool_needed": "correlation_analysis",
                    "params": {"columns": num_cols},
                    "status": "pending",
                    "requires_approval": False
                })
                step_num += 1

            if len(cat_cols) > 0 and len(num_cols) > 0:
                steps.append({
                    "step_number": step_num,
                    "action": "Generate Category Bar Chart",
                    "description": f"Plot bar chart of '{num_cols[0]}' by '{cat_cols[0]}'.",
                    "tool_needed": "bar_chart",
                    "params": {"x_col": cat_cols[0], "y_col": num_cols[0]},
                    "status": "pending",
                    "requires_approval": False
                })
                step_num += 1

        # Validation & Report steps
        steps.append({
            "step_number": step_num,
            "action": "Validate Findings",
            "description": "Perform validation audit, anti-hallucination check, and correlation vs causation audit.",
            "tool_needed": "validate_claims",
            "params": {},
            "status": "pending",
            "requires_approval": False
        })
        step_num += 1

        steps.append({
            "step_number": step_num,
            "action": "Generate Report",
            "description": "Synthesize final structured executive report.",
            "tool_needed": "generate_report",
            "params": {},
            "status": "pending",
            "requires_approval": False
        })

        return {
            "goal": question,
            "plan_steps": steps,
            "reasoning": f"Created {len(steps)}-step tailored plan for question: '{question}'."
        }

    def run_analysis(self, state: AgentState) -> AgentState:
        """
        Executes or resumes the iterative agent workflow loop using the LangGraph StateGraph.
        Preserves complete backward compatibility with the frontend and backend API contracts.
        """
        session_id = state.get("session_id") or f"sess-{int(time.time()*1000)}"
        state["session_id"] = session_id
        if "trace_logs" not in state:
            state["trace_logs"] = []
        if "observations" not in state:
            state["observations"] = []
        if "charts" not in state:
            state["charts"] = []
        if "completed" not in state:
            state["completed"] = False

        config = {"configurable": {"thread_id": session_id}}

        # Invoke the LangGraph StateGraph
        final_state = self.graph.invoke(state, config=config)

        # Merge results into state dict
        for k, v in final_state.items():
            state[k] = v

        return state
