from typing import Dict, Any
from app.tools.ml_tools import train_regression_model, train_classification_model, train_clustering_model

class MLAgent:
    def execute_tool(self, tool_name: str, file_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executes Scikit-learn ML training tool."""
        try:
            if tool_name in ["train_regression", "regression"]:
                result = train_regression_model(
                    file_path,
                    target_col=params.get("target_col", ""),
                    feature_cols=params.get("feature_cols"),
                    model_type=params.get("model_type", "random_forest")
                )
            elif tool_name in ["train_classification", "classification"]:
                result = train_classification_model(
                    file_path,
                    target_col=params.get("target_col", ""),
                    feature_cols=params.get("feature_cols"),
                    model_type=params.get("model_type", "random_forest")
                )
            elif tool_name in ["train_clustering", "clustering"]:
                result = train_clustering_model(
                    file_path,
                    feature_cols=params.get("feature_cols"),
                    n_clusters=params.get("n_clusters", 3)
                )
            else:
                return {"success": False, "summary": f"Unknown ML tool '{tool_name}'", "output_data": None}
                
            return {
                "tool_name": tool_name,
                "output_data": result,
                "summary": result.get("summary", "ML tool executed successfully."),
                "success": "error" not in result
            }
        except Exception as e:
            return {
                "tool_name": tool_name,
                "output_data": None,
                "summary": f"Error executing ML tool {tool_name}: {str(e)}",
                "success": False
            }
