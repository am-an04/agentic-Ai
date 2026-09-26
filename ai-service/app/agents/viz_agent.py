from typing import Dict, Any
from app.tools.viz_tools import create_bar_chart, create_line_chart, create_scatter_plot, create_box_plot, create_heatmap

class VisualizationAgent:
    def execute_tool(self, tool_name: str, file_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executes visualization tool and generates Plotly chart specification."""
        try:
            if tool_name == "bar_chart":
                result = create_bar_chart(
                    file_path, 
                    x_col=params.get("x_col", ""), 
                    y_col=params.get("y_col", ""),
                    color_col=params.get("color_col"),
                    title=params.get("title", "")
                )
            elif tool_name == "line_chart":
                result = create_line_chart(
                    file_path, 
                    x_col=params.get("x_col", ""), 
                    y_col=params.get("y_col", ""),
                    color_col=params.get("color_col"),
                    title=params.get("title", "")
                )
            elif tool_name == "scatter_plot":
                result = create_scatter_plot(
                    file_path, 
                    x_col=params.get("x_col", ""), 
                    y_col=params.get("y_col", ""),
                    color_col=params.get("color_col"),
                    title=params.get("title", "")
                )
            elif tool_name == "box_plot":
                result = create_box_plot(
                    file_path, 
                    category_col=params.get("category_col", ""), 
                    value_col=params.get("value_col", ""),
                    title=params.get("title", "")
                )
            elif tool_name == "heatmap":
                result = create_heatmap(file_path, title=params.get("title", "Correlation Heatmap"))
            else:
                return {"success": False, "summary": f"Unknown visualization tool '{tool_name}'", "output_data": None}
                
            return {
                "tool_name": tool_name,
                "output_data": result,
                "summary": result.get("summary", "Chart generated successfully."),
                "success": "error" not in result
            }
        except Exception as e:
            return {
                "tool_name": tool_name,
                "output_data": None,
                "summary": f"Error generating chart {tool_name}: {str(e)}",
                "success": False
            }
