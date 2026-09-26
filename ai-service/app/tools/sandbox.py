import pandas as pd
import numpy as np
from typing import Dict, Any
from app.tools.profiling_tools import load_dataset

class SandboxExecutionError(Exception):
    pass

def execute_controlled_python(file_path: str, code_snippet: str) -> Dict[str, Any]:
    """
    Executes a controlled Python code snippet against a loaded DataFrame.
    Restricts access to dangerous modules (os, sys, subprocess, builtins) for safety.
    """
    df = load_dataset(file_path)
    
    # Safe global context
    safe_globals = {
        "__builtins__": {
            "len": len, "sum": sum, "max": max, "min": min, "abs": abs,
            "round": round, "range": range, "list": list, "dict": dict,
            "set": set, "str": str, "int": int, "float": float, "bool": bool,
            "zip": zip, "enumerate": enumerate, "print": print
        },
        "pd": pd,
        "np": np,
        "df": df,
        "result": None
    }

    # Block illegal keywords
    blacklisted = ["import os", "import sys", "import subprocess", "__import__", "eval(", "exec(", "open(", "socket"]
    for word in blacklisted:
        if word in code_snippet:
            raise SandboxExecutionError(f"Security restriction: Execution of forbidden code '{word}' is blocked.")

    try:
        # Wrap snippet to capture output in local 'result'
        exec(code_snippet, safe_globals)
        res = safe_globals.get("result")
        
        # Serialize pandas objects
        if isinstance(res, pd.DataFrame):
            res_data = res.head(50).to_dict(orient="records")
        elif isinstance(res, pd.Series):
            res_data = res.head(50).to_dict()
        else:
            res_data = res
            
        return {
            "success": True,
            "result": res_data,
            "summary": f"Executed snippet successfully. Result type: {type(res).__name__}."
        }
    except Exception as e:
        return {
            "success": False,
            "result": None,
            "summary": f"Sandbox execution error: {str(e)}"
        }
