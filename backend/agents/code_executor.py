"""
Code Executor Agent: LLM writes Python code, executed in a restricted subprocess.
"""

import json
import tempfile
import subprocess
import os
import pickle
from pathlib import Path

import pandas as pd
from openai import AsyncOpenAI
from config import settings
from agents.state import AgentState


_client = AsyncOpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
)

CODE_SYSTEM_PROMPT = """You are a Python data science code generator. Given a user's request and dataset information, write Python code that operates on a pandas DataFrame variable called `df`.

## RULES:
1. The variable `df` is already loaded — do NOT read from files.
2. You can import from: pandas, numpy, datetime, re, math. No other imports.
3. Do NOT use: os, sys, subprocess, open(), exec(), eval(), __import__, requests, urllib, or any file/network operations.
4. Print results using print(). If the result is a DataFrame, assign it to a variable called `result_df`.
5. Keep code concise and well-commented.
6. RESPOND WITH ONLY THE PYTHON CODE. No markdown, no explanation, no code fences.

Example:
import numpy as np
from datetime import datetime
# Calculate monthly averages
monthly_avg = df.groupby('month')['sales'].mean()
print("Monthly Averages:")
print(monthly_avg)
result_df = monthly_avg.reset_index()
"""

# Blocklist for dangerous imports/functions - relaxed to allow common data science patterns
BLOCKED_PATTERNS = [
    "import os", "import sys", "import subprocess", "import shutil",
    "import socket", "import http", "import urllib", "import requests",
    "import webbrowser",
    "__import__", "exec(", "eval(", "compile(",
    "os.system", "os.popen", "subprocess.",
    "shutil.", "socket.", "globals(", "locals(",
]


def _validate_code(code: str) -> tuple[bool, str]:
    """Check code for dangerous patterns."""
    for pattern in BLOCKED_PATTERNS:
        if pattern in code:
            return False, f"Blocked pattern detected: {pattern}"
    return True, ""


async def code_executor_node(state: AgentState) -> dict:
    """Generate and execute Python code with retry logic."""
    events = []
    events.append({"event": "status", "data": "Writing Python code..."})

    df = state.get("dataframe")
    summary = state.get("dataframe_summary", {})

    if df is None:
        return {
            "sse_events": [{"event": "error", "data": "No data loaded for code execution."}],
            "result": None,
        }

    # Ask LLM to write code with retry logic
    context = f"""Dataset columns: {list(df.columns)}
Column types: {json.dumps(summary.get('dtypes', {}), default=str)}
Shape: {len(df)} rows × {len(df.columns)} columns
Sample data (first 5 rows):
{df.head(5).to_string()}"""

    max_retries = 2
    code = None
    last_error = None
    
    for attempt in range(max_retries + 1):
        messages = [
            {"role": "system", "content": CODE_SYSTEM_PROMPT},
            {"role": "user", "content": f"Data:\n{context}\n\nRequest: {state['user_message']}"},
        ]
        
        # Add error feedback on retries
        if attempt > 0 and last_error:
            messages.append({
                "role": "user", 
                "content": f"Previous attempt failed with error: {last_error}. Please fix the code and try again."
            })

        try:
            response = await _client.chat.completions.create(
                model=settings.llm_model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=1500,
            )
            code = response.choices[0].message.content.strip()

            # Clean markdown fences
            if code.startswith("```"):
                lines = code.split("\n")
                code = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
                if code.startswith("python"):
                    code = code[6:].strip()

            # Validate
            is_safe, reason = _validate_code(code)
            if not is_safe:
                last_error = f"Safety check failed: {reason}"
                if attempt == max_retries:
                    events.append({"event": "error", "data": f"Generated code was blocked for safety: {reason}"})
                    return {"sse_events": events, "result": None}
                continue
                
            break  # Success - exit retry loop

        except Exception as e:
            last_error = str(e)
            if attempt == max_retries:
                events.append({"event": "error", "data": "Failed to generate code after multiple attempts. Please try again."})
                return {"sse_events": events, "result": None}

    events.append({"event": "status", "data": "Executing code..."})

    # Execute in subprocess
    try:
        result = _execute_code(code, df)
        code_output = {
            "code": code,
            "stdout": result.get("stdout", ""),
            "error": result.get("error"),
            "result_table": result.get("result_table"),
        }

        events.append({"event": "code_output", "data": json.dumps(code_output, default=str)})

        if result.get("error"):
            # Retry once on execution error
            if "name '" in result["error"] or "SyntaxError" in result["error"]:
                events.append({"event": "status", "data": "Fixing code error..."})
                # Could add another retry here with error feedback
            events.append({"event": "text", "data": json.dumps({
                "agent_name": "Code Executor",
                "content": f"Code executed with an error: {result['error']}",
            })})
        else:
            events.append({"event": "text", "data": json.dumps({
                "agent_name": "Code Executor",
                "content": "Code executed successfully. See the output on the canvas.",
            })})

        return {
            "sse_events": events,
            "result": {"type": "code_output", "data": code_output},
        }

    except Exception as e:
        events.append({"event": "error", "data": "Code execution failed. Try a different approach."})
        return {"sse_events": events, "result": None}


def _execute_code(code: str, df: pd.DataFrame) -> dict:
    """Execute Python code in a subprocess with timeout."""

    # Create temp directory for data exchange
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save DataFrame for the subprocess
        data_path = os.path.join(tmpdir, "input_data.pkl")
        result_path = os.path.join(tmpdir, "result_data.pkl")
        df.to_pickle(data_path)

        # Build the execution script
        script = f"""
import pandas as pd
import numpy as np
import pickle
import sys

# Load the DataFrame
df = pd.read_pickle(r"{data_path}")

# User code
{code}

# Save result_df if it exists
if 'result_df' in dir():
    rd = result_df
    if isinstance(rd, pd.DataFrame):
        rd.to_pickle(r"{result_path}")
    elif isinstance(rd, pd.Series):
        rd.to_frame().to_pickle(r"{result_path}")
"""

        script_path = os.path.join(tmpdir, "run_code.py")
        with open(script_path, "w") as f:
            f.write(script)

        # Execute with timeout
        try:
            proc = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=tmpdir,
            )

            result = {"stdout": proc.stdout, "error": None, "result_table": None}

            if proc.returncode != 0:
                # Extract a clean error message
                stderr = proc.stderr
                # Get the last line that looks like an error
                error_lines = [l for l in stderr.split("\n") if l.strip()]
                if error_lines:
                    result["error"] = error_lines[-1]
                else:
                    result["error"] = "Code execution failed."

            # Check for result DataFrame
            if os.path.exists(result_path):
                result_df = pd.read_pickle(result_path)
                result["result_table"] = {
                    "columns": list(result_df.columns),
                    "rows": result_df.head(100).where(result_df.head(100).notna(), None).to_dict(orient="records"),
                    "total_rows": len(result_df),
                }

            return result

        except subprocess.TimeoutExpired:
            return {"stdout": "", "error": "Code execution timed out (15s limit).", "result_table": None}
        except Exception as e:
            return {"stdout": "", "error": f"Execution error: {str(e)}", "result_table": None}
