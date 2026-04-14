"""
Sheets Copilot Service
Direct Code Generation for Read/Write operations on the grid.
NO AGENTIC BEHAVIOR - Just translate NL -> Pandas Code -> Execute -> Return Result
"""
import json
from typing import Dict, Any, List, Optional
from .sandbox import CodeSandbox

class SheetsCopilot:
    def __init__(self, llm_client, sandbox: CodeSandbox):
        self.llm = llm_client
        self.sandbox = sandbox
        
    def _get_context_prompt(self) -> str:
        """Generate a concise data profile for the LLM."""
        profile = self.sandbox.get_profile()
        
        context = f"""
### DATA PROFILE (USE THIS EXACTLY)
- **Shape**: {profile['shape'][0]} rows, {profile['shape'][1]} columns
- **Columns**: {profile['columns']}
- **Column Indices**: {{col: idx for idx, col in enumerate({profile['columns']})}}
- **Dtypes**: {profile['dtypes']}
- **Sample Data (First 3 rows)**:
{json.dumps(profile['head'], indent=2)}
- **Numeric Stats**: {json.dumps(profile['stats'], indent=2)[:500]}...

### INSTRUCTIONS
1. Write PURE PANDAS CODE to perform the requested operation.
2. For READ operations: Filter/select data and print the result.
3. For WRITE operations: Modify the 'df' dataframe directly (e.g., df['col'] = ...).
4. DO NOT use plots, complex agents, or multi-step planning.
5. Output ONLY the code block, no explanations.
6. Use exact column names from the profile above.
"""
        return context

    def process_request(self, user_query: str) -> Dict[str, Any]:
        """
        Process a natural language request for sheet read/write.
        Returns: {success: bool, data: dict|None, error: str|None, code: str}
        """
        system_prompt = "You are a Pandas Code Generator for spreadsheet operations. Output ONLY python code."
        user_prompt = f"{self._get_context_prompt()}\n\nUSER REQUEST: {user_query}"
        
        # Generate code
        try:
            response = self.llm.generate(
                system=system_prompt,
                user=user_prompt,
                temperature=0.0,  # Low temp for deterministic code
                max_tokens=500
            )
            
            # Extract code block
            code = response.strip()
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
                
            # Execute in sandbox
            success, result, logs = self.sandbox.execute(code)
            
            if success:
                # Return updated data for the frontend
                return {
                    "success": True,
                    "data": self.sandbox.df.head(100).to_dict(orient="records"),
                    "code": code,
                    "logs": logs,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "data": None,
                    "code": code,
                    "logs": logs,
                    "error": result  # Error message
                }
                
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "code": "",
                "logs": [],
                "error": str(e)
            }
