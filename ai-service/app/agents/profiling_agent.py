from typing import Dict, Any
from app.tools.profiling_tools import profile_dataset

class DataProfilingAgent:
    def execute(self, dataset_path: str) -> Dict[str, Any]:
        """Runs dataset profiling tool and constructs structured agent observation."""
        try:
            profile = profile_dataset(dataset_path)
            
            # Format high-level summary string
            num_cols_str = ", ".join(profile["numerical_columns"][:5])
            cat_cols_str = ", ".join(profile["categorical_columns"][:5])
            date_cols_str = ", ".join(profile["date_columns"]) if profile["date_columns"] else "None"
            targets_str = ", ".join(profile["potential_targets"]) if profile["potential_targets"] else "None"
            
            summary = (
                f"Dataset '{profile['dataset_name']}' loaded successfully. "
                f"Shape: {profile['row_count']} rows x {profile['col_count']} columns. "
                f"Numerical columns ({len(profile['numerical_columns'])}): [{num_cols_str}]. "
                f"Categorical columns ({len(profile['categorical_columns'])}): [{cat_cols_str}]. "
                f"Date columns: [{date_cols_str}]. "
                f"Potential target variables: [{targets_str}]. "
                f"Data quality score: {profile['data_quality_score']}/100."
            )
            
            return {
                "tool_name": "profile_dataset",
                "profile_data": profile,
                "summary": summary,
                "success": True
            }
        except Exception as e:
            return {
                "tool_name": "profile_dataset",
                "profile_data": None,
                "summary": f"Failed to profile dataset: {str(e)}",
                "success": False
            }
