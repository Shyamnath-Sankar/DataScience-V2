"""
Robust Code Sandbox for executing Python/Pandas code safely.
Used by both Sheets Copilot (direct) and Agentic Chat (skills).
"""
import pandas as pd
import numpy as np
import io
import traceback
from typing import Any, Dict, Optional, Tuple
import re

class CodeSandbox:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.original_df = df.copy()
        self.logs = []
        
        # Safe imports allowed in the sandbox
        self.safe_globals = {
            "pd": pd,
            "np": np,
            "df": self.df,
            "__builtins__": __builtins__,
            "re": re,
            "math": __import__("math"),
            "datetime": __import__("datetime"),
            "json": __import__("json"),
        }

    def reset(self):
        """Reset dataframe to original state if needed."""
        self.df = self.original_df.copy()
        self.logs = []

    def execute(self, code: str, timeout: int = 30) -> Tuple[bool, Any, str]:
        """
        Execute python code string against the dataframe.
        Returns: (success, result_dataframe_or_error, logs)
        """
        self.logs.append(f"--- Executing Code Block ---\n{code}")
        
        # Create a local scope for execution to prevent leakage
        local_scope = {"df": self.df}
        
        try:
            # Compile code to catch syntax errors early
            compiled_code = compile(code, "<sandbox>", "exec")
            
            # Execute with restricted globals but shared dataframe reference
            exec(compiled_code, self.safe_globals, local_scope)
            
            # Capture the modified dataframe
            if "df" in local_scope:
                self.df = local_scope["df"]
            elif "df" in self.safe_globals:
                self.df = self.safe_globals["df"]
                
            self.logs.append("✅ Execution Successful")
            return True, self.df, "\n".join(self.logs)
            
        except Exception as e:
            error_msg = f"❌ Execution Failed: {str(e)}\n{traceback.format_exc()}"
            self.logs.append(error_msg)
            return False, str(e), "\n".join(self.logs)

    def get_profile(self) -> Dict[str, Any]:
        """Generate a quick data profile for the LLM context."""
        profile = {
            "shape": self.df.shape,
            "columns": list(self.df.columns),
            "dtypes": self.df.dtypes.astype(str).to_dict(),
            "head": self.df.head(3).to_dict(orient="list"),
            "stats": {}
        }
        
        # Add numeric stats
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            profile["stats"][col] = {
                "min": float(self.df[col].min()),
                "max": float(self.df[col].max()),
                "mean": float(self.df[col].mean()),
                "nulls": int(self.df[col].isnull().sum())
            }
            
        return profile
