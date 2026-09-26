from typing import Dict, Any
from app.tools.stats_tools import two_sample_ttest, chi_square_test, anova_test

class StatisticsAgent:
    def execute_tool(self, tool_name: str, file_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executes statistical test tool and formats contextual results."""
        try:
            if tool_name == "ttest":
                result = two_sample_ttest(
                    file_path, 
                    group_col=params.get("group_col", ""), 
                    value_col=params.get("value_col", "")
                )
            elif tool_name == "chi_square":
                result = chi_square_test(
                    file_path, 
                    col1=params.get("col1", ""), 
                    col2=params.get("col2", "")
                )
            elif tool_name == "anova":
                result = anova_test(
                    file_path, 
                    group_col=params.get("group_col", ""), 
                    value_col=params.get("value_col", "")
                )
            else:
                return {"success": False, "summary": f"Unknown statistical tool '{tool_name}'", "output_data": None}
                
            return {
                "tool_name": tool_name,
                "output_data": result,
                "summary": result.get("summary", "Statistical test completed."),
                "success": "error" not in result
            }
        except Exception as e:
            return {
                "tool_name": tool_name,
                "output_data": None,
                "summary": f"Error executing statistical test {tool_name}: {str(e)}",
                "success": False
            }
