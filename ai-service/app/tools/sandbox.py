"""
Secure Subprocess Sandbox for Model-Generated Python Execution.
Executes Pandas/NumPy code in an isolated subprocess with AST safety validation,
execution time limits, read-only dataset access, and no file/network writing.
"""

import ast
import sys
import json
import os
import subprocess
from typing import Dict, Any, Optional

ALLOWED_MODULES = {"pandas", "numpy", "math", "scipy", "datetime", "json", "re"}
FORBIDDEN_CALLS = {
    "eval", "exec", "open", "compile", "__import__",
    "getattr", "setattr", "delattr", "globals", "locals",
    "breakpoint", "input", "system", "popen", "spawn"
}
FORBIDDEN_ATTRIBUTES = {
    "to_csv", "to_excel", "to_sql", "to_parquet", "to_pickle", "to_feather", "to_hdf"
}

class SandboxExecutionError(Exception):
    pass

def validate_code_ast(code_snippet: str):
    """
    Parses Python code snippet into an Abstract Syntax Tree (AST) and verifies:
    - No forbidden imports (only allowed: pandas, numpy, math, scipy, datetime, json, re)
    - No dangerous builtins (eval, exec, open, getattr, etc.)
    - No dunder introspection (__subclasses__, __globals__, etc.)
    - No filesystem writing methods (to_csv, to_excel, etc.)
    """
    try:
        tree = ast.parse(code_snippet)
    except SyntaxError as syn_err:
        raise SandboxExecutionError(f"Syntax error in code snippet: {syn_err}")

    for node in ast.walk(tree):
        # 1. Check imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split('.')[0]
                if root_pkg not in ALLOWED_MODULES:
                    raise SandboxExecutionError(f"Security violation: Import of '{alias.name}' is prohibited in sandbox.")

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split('.')[0]
                if root_pkg not in ALLOWED_MODULES:
                    raise SandboxExecutionError(f"Security violation: Import from '{node.module}' is prohibited in sandbox.")

        # 2. Check forbidden function calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_CALLS:
                    raise SandboxExecutionError(f"Security violation: Call to '{node.func.id}' is prohibited in sandbox.")

        # 3. Check forbidden attributes & dunder reflection
        elif isinstance(node, ast.Attribute):
            attr_name = node.attr
            if attr_name.startswith("__") and attr_name.endswith("__"):
                raise SandboxExecutionError(f"Security violation: Special attribute '{attr_name}' access is prohibited.")
            if attr_name in FORBIDDEN_ATTRIBUTES:
                raise SandboxExecutionError(f"Security violation: File write method '{attr_name}' is blocked in read-only sandbox.")

SUBPROCESS_RUNNER_SCRIPT = r"""
import sys
import json
import math
import numpy as np
import pandas as pd

file_path = sys.argv[1]
code_snippet = sys.stdin.read()

# Load dataset read-only
if file_path.endswith('.csv'):
    df = pd.read_csv(file_path)
elif file_path.endswith(('.xls', '.xlsx')):
    df = pd.read_excel(file_path)
else:
    df = pd.read_csv(file_path)

safe_globals = {
    "__builtins__": {
        "len": len, "sum": sum, "max": max, "min": min, "abs": abs,
        "round": round, "range": range, "list": list, "dict": dict,
        "set": set, "str": str, "int": int, "float": float, "bool": bool,
        "zip": zip, "enumerate": enumerate, "print": print, "sorted": sorted
    },
    "pd": pd,
    "np": np,
    "math": math,
    "df": df,
    "result": None
}

try:
    exec(code_snippet, safe_globals)
    res = safe_globals.get("result")

    def sanitize(obj):
        if isinstance(obj, (np.floating, float)):
            return None if math.isnan(obj) or math.isinf(obj) else float(obj)
        if isinstance(obj, (np.integer, int)):
            return int(obj)
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, pd.DataFrame):
            return [sanitize(r) for r in obj.head(50).to_dict(orient="records")]
        if isinstance(obj, pd.Series):
            return {str(k): sanitize(v) for k, v in obj.head(50).to_dict().items()}
        if isinstance(obj, dict):
            return {str(k): sanitize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [sanitize(v) for v in obj]
        return str(obj) if not isinstance(obj, (str, type(None))) else obj

    output = {
        "success": True,
        "result": sanitize(res),
        "result_type": type(res).__name__,
        "error": None
    }
except Exception as e:
    output = {
        "success": False,
        "result": None,
        "result_type": "None",
        "error": str(e)
    }

print("___SANDBOX_OUT___")
print(json.dumps(output))
"""

def execute_controlled_python(file_path: str, code_snippet: str, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Executes a controlled Python code snippet against a loaded dataset in an isolated subprocess.
    Enforces AST validation, a 5-second execution limit, read-only data access, and no network/disk writes.
    """
    if not os.path.exists(file_path):
        return {
            "success": False,
            "result": None,
            "summary": f"Dataset file not found at: {file_path}"
        }

    # Step 1: AST validation
    try:
        validate_code_ast(code_snippet)
    except SandboxExecutionError as sec_err:
        return {
            "success": False,
            "result": None,
            "error": str(sec_err),
            "summary": f"Sandbox security rejection: {str(sec_err)}"
        }

    # Step 2: Isolated Subprocess execution
    try:
        proc = subprocess.run(
            [sys.executable, "-c", SUBPROCESS_RUNNER_SCRIPT, file_path],
            input=code_snippet,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        stdout = proc.stdout
        stderr = proc.stderr

        if "___SANDBOX_OUT___" in stdout:
            parts = stdout.split("___SANDBOX_OUT___")
            out_json = parts[-1].strip()
            parsed = json.loads(out_json)
            if parsed.get("success"):
                return {
                    "success": True,
                    "result": parsed.get("result"),
                    "result_type": parsed.get("result_type"),
                    "summary": f"Executed code successfully. Result type: {parsed.get('result_type')}."
                }
            else:
                return {
                    "success": False,
                    "result": None,
                    "error": parsed.get("error"),
                    "summary": f"Runtime error in code snippet: {parsed.get('error')}"
                }
        else:
            err_msg = stderr.strip() or stdout.strip() or "Process terminated without output."
            return {
                "success": False,
                "result": None,
                "error": err_msg,
                "summary": f"Sandbox process error: {err_msg}"
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "result": None,
            "error": f"Execution timeout ({timeout}s limit exceeded)",
            "summary": f"Security restriction: Execution exceeded {timeout}s CPU timeout."
        }
    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": str(e),
            "summary": f"Sandbox unexpected execution error: {str(e)}"
        }
