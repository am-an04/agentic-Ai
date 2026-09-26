import time
import os
from typing import Dict, Any, List
from app.core.state import AgentState
from app.agents.profiling_agent import DataProfilingAgent
from app.agents.eda_agent import EDAAgent
from app.agents.stats_agent import StatisticsAgent
from app.agents.ml_agent import MLAgent
from app.agents.viz_agent import VisualizationAgent
from app.agents.validation_agent import ValidationAgent
from app.agents.report_agent import ReportGenerationAgent

class AgentOrchestrator:
    def __init__(self):
        self.profiler = DataProfilingAgent()
        self.eda_agent = EDAAgent()
        self.stats_agent = StatisticsAgent()
        self.ml_agent = MLAgent()
        self.viz_agent = VisualizationAgent()
        self.validation_agent = ValidationAgent()
        self.report_agent = ReportGenerationAgent()

    def create_plan(self, question: str, profile: Dict[str, Any], enable_ml: bool = True) -> Dict[str, Any]:
        """Creates a dynamic, goal-oriented analysis plan based on user query and dataset profiling."""
        q_lower = question.lower()
        cols = profile.get("columns", [])
        num_cols = profile.get("numerical_columns", [])
        cat_cols = profile.get("categorical_columns", [])
        date_cols = profile.get("date_columns", [])

        steps = []
        step_num = 1

        # 1. Profiling (always completed)
        steps.append({
            "step_number": step_num,
            "action": "Profile Dataset",
            "description": f"Inspected dataset shape ({profile.get('row_count')} rows x {profile.get('col_count')} cols) and data quality.",
            "tool_needed": "profile_dataset",
            "status": "completed"
        })
        step_num += 1

        # Scenario A: Sales / Trend / Q3 Decline
        if any(kw in q_lower for kw in ["sales", "revenue", "q3", "decrease", "decline", "trend", "fall"]):
            date_col = date_cols[0] if date_cols else (cols[1] if len(cols) > 1 else "order_date")
            val_col = "revenue" if "revenue" in cols else (num_cols[0] if num_cols else "sales")
            cat_col = cat_cols[0] if cat_cols else "region"

            steps.append({
                "step_number": step_num,
                "action": "Analyze Quarterly Trend",
                "description": f"Calculate quarterly aggregated sum and period-over-period percentage change for '{val_col}' over '{date_col}'.",
                "tool_needed": "trend_analysis",
                "params": {"date_col": date_col, "value_col": val_col, "freq": "Q"},
                "status": "pending"
            })
            step_num += 1

            if len(cat_cols) > 0:
                steps.append({
                    "step_number": step_num,
                    "action": "Investigate Categorical Performance",
                    "description": f"Group '{val_col}' by '{cat_col}' to isolate underperforming segments.",
                    "tool_needed": "group_by_analysis",
                    "params": {"group_col": cat_col, "target_col": val_col, "agg_funcs": ["sum", "mean", "count"]},
                    "status": "pending"
                })
                step_num += 1

            if len(cat_cols) > 1:
                steps.append({
                    "step_number": step_num,
                    "action": "Investigate Secondary Category Anomaly",
                    "description": f"Group '{val_col}' by '{cat_cols[1]}' to detect product/segment level drop.",
                    "tool_needed": "group_by_analysis",
                    "params": {"group_col": cat_cols[1], "target_col": val_col, "agg_funcs": ["sum", "mean", "count"]},
                    "status": "pending"
                })
                step_num += 1

            if len(num_cols) >= 2:
                steps.append({
                    "step_number": step_num,
                    "action": "Correlation Analysis on Factors",
                    "description": f"Compute correlations between '{val_col}' and numeric factors.",
                    "tool_needed": "correlation_analysis",
                    "params": {"columns": num_cols},
                    "status": "pending"
                })
                step_num += 1

            # Stats test
            if len(cat_cols) > 0 and len(num_cols) > 0:
                steps.append({
                    "step_number": step_num,
                    "action": "Statistical Hypothesis Test",
                    "description": f"Perform ANOVA/t-test comparing '{val_col}' across '{cat_col}'.",
                    "tool_needed": "anova",
                    "params": {"group_col": cat_col, "value_col": val_col},
                    "status": "pending"
                })
                step_num += 1

            # Visualizations
            steps.append({
                "step_number": step_num,
                "action": "Generate Quarterly Trend Chart",
                "description": f"Plot interactive line chart of '{val_col}' quarterly trend.",
                "tool_needed": "line_chart",
                "params": {"x_col": date_col, "y_col": val_col, "title": "Quarterly Revenue Trend"},
                "status": "pending"
            })
            step_num += 1

        # Scenario B: Churn / Drivers / Association
        elif any(kw in q_lower for kw in ["churn", "factor", "associate", "predict", "driver"]):
            target = "churn_risk" if "churn_risk" in cols else (num_cols[0] if num_cols else cols[-1])

            steps.append({
                "step_number": step_num,
                "action": "Analyze Feature Correlations",
                "description": f"Compute correlation matrix against target variable '{target}'.",
                "tool_needed": "correlation_analysis",
                "params": {"columns": num_cols},
                "status": "pending"
            })
            step_num += 1

            if len(cat_cols) >= 2:
                steps.append({
                    "step_number": step_num,
                    "action": "Chi-Square Test of Association",
                    "description": f"Test association between '{cat_cols[0]}' and categorical target.",
                    "tool_needed": "chi_square",
                    "params": {"col1": cat_cols[0], "col2": target if target in cat_cols else cat_cols[-1]},
                    "status": "pending"
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
                "status": "pending"
            })
            step_num += 1

        # Scenario C: Customer Segmentation / Clustering
        elif any(kw in q_lower for kw in ["segment", "cluster", "group"]):
            if enable_ml and len(num_cols) >= 2:
                steps.append({
                    "step_number": step_num,
                    "action": "K-Means Clustering Segmentation",
                    "description": "Perform K-Means clustering to discover customer segments.",
                    "tool_needed": "train_clustering",
                    "params": {"feature_cols": num_cols, "n_clusters": 3},
                    "requires_approval": True,
                    "status": "pending"
                })
                step_num += 1

            if len(num_cols) >= 2:
                steps.append({
                    "step_number": step_num,
                    "action": "Scatter Plot Visualization",
                    "description": f"Plot scatter relationship between '{num_cols[0]}' and '{num_cols[1]}'.",
                    "tool_needed": "scatter_plot",
                    "params": {"x_col": num_cols[0], "y_col": num_cols[1], "title": "Customer Segment Clusters"},
                    "status": "pending"
                })
                step_num += 1

        # Scenario D: Generic Exploratory Analysis
        else:
            if len(num_cols) > 0:
                steps.append({
                    "step_number": step_num,
                    "action": "Distribution Analysis",
                    "description": f"Analyze distribution of metric '{num_cols[0]}'.",
                    "tool_needed": "distribution_analysis",
                    "params": {"column": num_cols[0]},
                    "status": "pending"
                })
                step_num += 1

            if len(num_cols) >= 2:
                steps.append({
                    "step_number": step_num,
                    "action": "Correlation Matrix",
                    "description": "Calculate correlation matrix for numerical variables.",
                    "tool_needed": "correlation_analysis",
                    "params": {"columns": num_cols},
                    "status": "pending"
                })
                step_num += 1

            if len(cat_cols) > 0 and len(num_cols) > 0:
                steps.append({
                    "step_number": step_num,
                    "action": "Category Group-by Aggregation",
                    "description": f"Group '{num_cols[0]}' by '{cat_cols[0]}'.",
                    "tool_needed": "group_by_analysis",
                    "params": {"group_col": cat_cols[0], "target_col": num_cols[0]},
                    "status": "pending"
                })
                step_num += 1

            if len(cat_cols) > 0 and len(num_cols) > 0:
                steps.append({
                    "step_number": step_num,
                    "action": "Generate Category Bar Chart",
                    "description": f"Plot bar chart of '{num_cols[0]}' by '{cat_cols[0]}'.",
                    "tool_needed": "bar_chart",
                    "params": {"x_col": cat_cols[0], "y_col": num_cols[0]},
                    "status": "pending"
                })
                step_num += 1

        # Final Validation & Report steps
        steps.append({
            "step_number": step_num,
            "action": "Validate Findings",
            "description": "Perform validation audit, anti-hallucination check, and correlation vs causation audit.",
            "tool_needed": "validate_claims",
            "status": "pending"
        })
        step_num += 1

        steps.append({
            "step_number": step_num,
            "action": "Generate Report",
            "description": "Synthesize final structured executive report.",
            "tool_needed": "generate_report",
            "status": "pending"
        })

        return {
            "goal": question,
            "plan_steps": steps,
            "reasoning": f"Created {len(steps)}-step tailored plan for question: '{question}'."
        }

    def run_analysis(self, state: AgentState) -> AgentState:
        """Runs the complete iterative agentic workflow loop."""
        file_path = state["dataset_path"]
        question = state["user_question"]

        # Step 1: Profile
        state["trace_logs"].append({
            "step": "Understand & Profile",
            "description": "Inspecting dataset metrics and columns...",
            "timestamp": time.time()
        })
        prof_res = self.profiler.execute(file_path)
        state["profile"] = prof_res["profile_data"]
        
        # Step 2: Plan
        state["trace_logs"].append({
            "step": "Create Plan",
            "description": f"Formulating analytical workflow for: '{question}'",
            "timestamp": time.time()
        })
        plan = self.create_plan(question, state["profile"])
        state["plan"] = plan

        # Step 3: Iterate through plan steps
        for step in plan["plan_steps"]:
            tool_name = step.get("tool_needed")
            params = step.get("params", {})

            if tool_name == "profile_dataset":
                continue

            # Check for Human-in-the-Loop approval
            if step.get("requires_approval") and not state.get("is_approved"):
                state["requires_human_approval"] = True
                state["approval_prompt"] = f"Action '{step['action']}' ({tool_name}) requires confirmation. Proceed with Machine Learning training?"
                state["trace_logs"].append({
                    "step": "Human Approval Required",
                    "description": state["approval_prompt"],
                    "timestamp": time.time()
                })
                # Pause execution for human input
                return state

            state["trace_logs"].append({
                "step": f"Executing Tool: {tool_name}",
                "description": step["description"],
                "timestamp": time.time()
            })

            # Route tool calls
            res = None
            if tool_name in ["correlation_analysis", "group_by_analysis", "trend_analysis", "distribution_analysis"]:
                res = self.eda_agent.execute_tool(tool_name, file_path, params)
            elif tool_name in ["ttest", "chi_square", "anova"]:
                res = self.stats_agent.execute_tool(tool_name, file_path, params)
            elif tool_name in ["train_regression", "train_classification", "train_clustering"]:
                res = self.ml_agent.execute_tool(tool_name, file_path, params)
            elif tool_name in ["bar_chart", "line_chart", "scatter_plot", "box_plot", "heatmap"]:
                res = self.viz_agent.execute_tool(tool_name, file_path, params)
                if res.get("success"):
                    state["charts"].append(res)
            elif tool_name == "validate_claims":
                v_res = self.validation_agent.validate(state["observations"], question)
                state["validation_result"] = v_res
                step["status"] = "completed"
                continue
            elif tool_name == "generate_report":
                r_res = self.report_agent.generate_report(
                    user_question=question,
                    profile=state["profile"],
                    observations=state["observations"],
                    charts=state["charts"],
                    validation_result=state.get("validation_result", {}),
                    trace_logs=state["trace_logs"]
                )
                state["final_report"] = r_res
                step["status"] = "completed"
                state["completed"] = True
                continue

            if res:
                step["status"] = "completed" if res.get("success") else "failed"
                state["observations"].append(res)

        return state
