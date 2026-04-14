"""
Agentic Chat System with Planner, Skills, and Task Execution.
Handles complex multi-step analysis (EDA, Data Science, Visualizations).
"""
import json
from typing import Dict, Any, List, Optional
from .sandbox import CodeSandbox

class Skill:
    """Base class for predefined skills like EDA, Data Science, etc."""
    def __init__(self, name: str, description: str, tasks: List[str]):
        self.name = name
        self.description = description
        self.tasks = tasks  # Pre-defined task templates

class EDASkill(Skill):
    def __init__(self):
        super().__init__(
            name="EDA",
            description="Exploratory Data Analysis including distributions, correlations, and outliers.",
            tasks=[
                "Analyze data shape, types, and missing values.",
                "Generate summary statistics for numeric columns.",
                "Identify correlations between variables (>0.5).",
                "Detect outliers using IQR or Z-Score methods.",
                "Visualize key distributions and relationships."
            ]
        )

class DataScienceSkill(Skill):
    def __init__(self):
        super().__init__(
            name="DataScience",
            description="Predictive modeling, regression, classification, and clustering.",
            tasks=[
                "Preprocess data (scaling, encoding, imputation).",
                "Split data into train/test sets.",
                "Train baseline models (Linear Regression, Random Forest).",
                "Evaluate model performance (RMSE, Accuracy, F1).",
                "Feature importance analysis."
            ]
        )

class AgenticChat:
    def __init__(self, llm_client, sandbox: CodeSandbox):
        self.llm = llm_client
        self.sandbox = sandbox
        self.skills = {
            "EDA": EDASkill(),
            "DataScience": DataScienceSkill()
        }
        self.task_history = []
        
    def _get_planner_prompt(self, user_query: str, available_skills: List[str]) -> str:
        return f"""
You are an AI Planner for Data Science tasks.
User Request: "{user_query}"

Available Skills: {available_skills}

Your Job:
1. Decide which Skill(s) are needed.
2. Break the request into a step-by-step plan of tasks.
3. Output a JSON list of tasks with assigned skills.

Example Output:
[
    {{"skill": "EDA", "task": "Analyze data shape, types, and missing values."}},
    {{"skill": "EDA", "task": "Generate summary statistics for numeric columns."}}
]
"""

    def _get_code_writer_prompt(self, task: str, skill_name: str, df_profile: dict) -> str:
        profile_str = json.dumps(df_profile, indent=2)[:1000]
        return f"""
You are a Code Writer for the '{skill_name}' skill.
Task to execute: "{task}"

Data Profile:
{profile_str}

Instructions:
1. Write Python code using pandas/numpy/sklearn/plotly to execute this task.
2. If plotting, save the figure to 'fig' variable.
3. If analysis, print clear results to stdout.
4. Modify 'df' if necessary.
5. Output ONLY the code block.
"""

    def plan(self, user_query: str) -> List[Dict[str, str]]:
        """Generate a plan of tasks based on user query."""
        prompt = self._get_planner_prompt(user_query, list(self.skills.keys()))
        
        try:
            response = self.llm.generate(
                system="You are a JSON-only planner. Output valid JSON list.",
                user=prompt,
                temperature=0.2,
                max_tokens=800
            )
            
            # Parse JSON
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
                
            plan = json.loads(response.strip())
            return plan
            
        except Exception as e:
            # Fallback simple plan
            return [{"skill": "EDA", "task": f"Analyze data to answer: {user_query}"}]

    def execute_task(self, task_def: Dict[str, str]) -> Dict[str, Any]:
        """Execute a single task using code generation."""
        skill_name = task_def.get("skill", "EDA")
        task_desc = task_def.get("task", "")
        
        # Get fresh profile
        profile = self.sandbox.get_profile()
        
        # Generate code
        prompt = self._get_code_writer_prompt(task_desc, skill_name, profile)
        
        try:
            code_response = self.llm.generate(
                system="You are a Python coding expert. Output only code.",
                user=prompt,
                temperature=0.1,
                max_tokens=600
            )
            
            # Extract code
            code = code_response.strip()
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
                
            # Execute
            success, result, logs = self.sandbox.execute(code)
            
            return {
                "task": task_desc,
                "skill": skill_name,
                "success": success,
                "code": code,
                "output": logs,
                "error": None if success else result
            }
            
        except Exception as e:
            return {
                "task": task_desc,
                "skill": skill_name,
                "success": False,
                "code": "",
                "output": "",
                "error": str(e)
            }

    def process_request(self, user_query: str) -> Dict[str, Any]:
        """
        Full agentic flow: Plan -> Execute Tasks -> Summarize
        Returns: {success, plan, results, summary}
        """
        # Step 1: Plan
        plan = self.plan(user_query)
        self.task_history.append({"query": user_query, "plan": plan})
        
        # Step 2: Execute each task
        results = []
        for task_def in plan:
            result = self.execute_task(task_def)
            results.append(result)
            if not result["success"]:
                # Optional: Stop on critical failure or continue
                pass
                
        # Step 3: Generate Summary (Walkthrough)
        summary_prompt = f"""
User Query: {user_query}
Plan: {json.dumps(plan)}
Execution Results:
{json.dumps(results, indent=2)}

Write a concise summary of findings and conclusions.
"""
        try:
            summary = self.llm.generate(
                system="Summarize the analysis results clearly.",
                user=summary_prompt,
                temperature=0.3,
                max_tokens=500
            )
        except:
            summary = "Analysis completed. Check individual task results."
            
        return {
            "success": all(r["success"] for r in results),
            "plan": plan,
            "results": results,
            "summary": summary
        }
