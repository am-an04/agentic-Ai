from typing import Dict, Any, List, Optional
from app.tools.eda_tools import correlation_analysis, group_by_analysis, trend_analysis, distribution_analysis

class EDAAgent:
    def execute_tool(self, tool_name: str, file_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executes selected EDA tool with given parameters."""
        try:
            if tool_name == "correlation_analysis":
                result = correlation_analysis(file_path, params.get("columns"))
            elif tool_name == "group_by_analysis":
                result = group_by_analysis(
                    file_path, 
                    group_col=params.get("group_col", ""), 
                    target_col=params.get("target_col", ""),
                    agg_funcs=params.get("agg_funcs", ["mean", "sum", "count"])
                )
            elif tool_name == "trend_analysis":
                result = trend_analysis(
                    file_path,
                    date_col=params.get("date_col", ""),
                    value_col=params.get("value_col", ""),
                    freq=params.get("freq", "Q")
                )
            elif tool_name == "distribution_analysis":
                result = distribution_analysis(file_path, column=params.get("column", ""))
            else:
                return {"success": False, "summary": f"Unknown EDA tool '{tool_name}'", "output_data": None}
                
            return {
                "tool_name": tool_name,
                "output_data": result,
                "summary": result.get("summary", "EDA tool completed successfully."),
                "success": "error" not in result
            }
        except Exception as e:
            return {
                "tool_name": tool_name,
                "output_data": None,
                "summary": f"Error executing {tool_name}: {str(e)}",
                "success": False
            }
