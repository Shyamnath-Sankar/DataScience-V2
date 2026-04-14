"""
Planner Agent: Decomposes complex requests into executable tasks using Skills.
Coordinates task execution, manages dependencies, and compiles results.
"""

import json
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
from config import settings
from agents.state import AgentState
from agents.skills import Skill, TaskTemplate, get_skill_by_keywords, SKILLS_REGISTRY


_client = AsyncOpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
)


PLANNER_SYSTEM_PROMPT = """You are a Planning Agent for a data science AI assistant. Your job is to:
1. Analyze the user's request and determine if it requires a multi-step plan
2. Select the appropriate Skill (EDA, Data Science, Visualization, Data Cleaning) or create a custom plan
3. Break down the request into executable tasks with proper dependencies
4. Track task completion and compile final results

## WHEN TO USE SKILLS:
- If the user asks for "EDA", "analyze data", "explore data" → Use EDA_SKILL
- If the user asks for "model", "prediction", "machine learning" → Use DATA_SCIENCE_SKILL  
- If the user asks for "visualize", "plot", "chart", "dashboard" → Use VISUALIZATION_SKILL
- If the user asks for "clean", "prepare", "fix data" → Use DATA_CLEANING_SKILL

## FOR SIMPLE REQUESTS:
If the request is simple (single question, quick calculation), don't create a plan - just return a single-task plan.

## OUTPUT FORMAT:
Respond with ONLY valid JSON in this exact format:
{
  "use_skill": "skill_id or null",
  "custom_tasks": [
    {
      "id": "task_1",
      "name": "Task Name",
      "description": "What this task does",
      "prompt": "Specific prompt for code generation",
      "expected_output_type": "code|text|chart|data",
      "dependencies": []
    }
  ],
  "reasoning": "Brief explanation of your plan"
}

Use custom_tasks only when no skill fits perfectly or for simple requests."""


async def plan_tasks(state: AgentState) -> dict:
    """
    Analyze user request and create a task plan.
    Returns plan with tasks to execute.
    """
    user_msg = state.get("user_message", "")
    df = state.get("dataframe")
    
    # Build context
    if df is not None:
        data_context = f"""Dataset: {len(df)} rows × {len(df.columns)} columns
Columns: {list(df.columns)}
Sample: {df.head(3).to_dict(orient='records')}"""
    else:
        data_context = "No dataset loaded"
    
    messages = [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "system", "content": f"DATA CONTEXT:\n{data_context}"},
        {"role": "user", "content": user_msg}
    ]
    
    try:
        response = await _client.chat.completions.create(
            model=settings.llm_model_name,
            messages=messages,
            temperature=0.1,
            max_tokens=1500,
        )
        
        plan_json = response.choices[0].message.content.strip()
        
        # Parse JSON
        if plan_json.startswith("```"):
            plan_json = plan_json.split("```")[1]
            if plan_json.startswith("json"):
                plan_json = plan_json[4:]
            plan_json = plan_json.strip()
        
        plan = json.loads(plan_json)
        
        # Validate plan structure
        if "custom_tasks" not in plan:
            plan["custom_tasks"] = []
        if "reasoning" not in plan:
            plan["reasoning"] = "Plan generated"
            
    except Exception as e:
        # Fallback: create minimal plan
        plan = {
            "use_skill": None,
            "custom_tasks": [{
                "id": "task_1",
                "name": "Answer Question",
                "description": "Process user request",
                "prompt": f"Answer: {user_msg}",
                "expected_output_type": "text",
                "dependencies": []
            }],
            "reasoning": f"Fallback plan due to error: {str(e)}"
        }
    
    # If skill specified, load task templates
    skill_id = plan.get("use_skill")
    selected_skill = None
    
    if skill_id and skill_id in SKILLS_REGISTRY:
        selected_skill = SKILLS_REGISTRY[skill_id]
    elif not skill_id and not plan.get("custom_tasks"):
        # Try to match skill by keywords
        matched_skill = get_skill_by_keywords([user_msg])
        if matched_skill:
            selected_skill = matched_skill
            plan["use_skill"] = matched_skill.id
    
    # Build final task list
    tasks_to_execute = []
    
    if selected_skill:
        # Use skill's predefined tasks
        for task in selected_skill.tasks:
            tasks_to_execute.append({
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "prompt": task.prompt_template,
                "expected_output_type": task.expected_output_type,
                "dependencies": task.dependencies,
                "skill_id": selected_skill.id
            })
    else:
        # Use custom tasks from LLM
        tasks_to_execute = plan.get("custom_tasks", [])
    
    # Ensure at least one task exists
    if not tasks_to_execute:
        tasks_to_execute = [{
            "id": "task_1",
            "name": "Process Request",
            "description": "Handle user query",
            "prompt": user_msg,
            "expected_output_type": "text",
            "dependencies": []
        }]
    
    return {
        "task_plan": {
            "skill_used": selected_skill.id if selected_skill else None,
            "tasks": tasks_to_execute,
            "reasoning": plan.get("reasoning", ""),
            "current_task_index": 0,
            "completed_tasks": [],
            "task_results": {}
        },
        "sse_events": [{
            "event": "status", 
            "data": f"Planning: {plan.get('reasoning', 'Creating task plan...')}"
        }]
    }


async def execute_next_task(state: AgentState) -> dict:
    """
    Execute the next pending task in the plan.
    Manages dependencies and tracks progress.
    """
    task_plan = state.get("task_plan", {})
    tasks = task_plan.get("tasks", [])
    current_idx = task_plan.get("current_task_index", 0)
    completed_tasks = set(task_plan.get("completed_tasks", []))
    task_results = task_plan.get("task_results", {})
    
    if current_idx >= len(tasks):
        # All tasks completed
        return {
            "sse_events": [{"event": "status", "data": "All tasks completed"}],
            "task_complete": True
        }
    
    current_task = tasks[current_idx]
    task_id = current_task["id"]
    
    # Check dependencies
    deps = current_task.get("dependencies", [])
    unmet_deps = [d for d in deps if d not in completed_tasks]
    
    if unmet_deps:
        # Skip this task, try next one
        task_plan["current_task_index"] = current_idx + 1
        return {
            "task_plan": task_plan,
            "sse_events": [{"event": "status", "data": f"Waiting for dependencies: {', '.join(unmet_deps)}"}]
        }
    
    # Build enhanced prompt with context from previous tasks
    base_prompt = current_task.get("prompt", "")
    context_from_previous = ""
    
    for dep_id in deps:
        if dep_id in task_results:
            result = task_results[dep_id]
            context_from_previous += f"\n\nResult from {dep_id}:\n{result.get('summary', result.get('output', 'No output'))}"
    
    enhanced_prompt = base_prompt + context_from_previous
    
    # Determine which agent should handle this task
    output_type = current_task.get("expected_output_type", "text")
    
    if output_type == "chart":
        target_agent = "visualization"
    elif output_type == "code":
        target_agent = "code"
    elif output_type == "data":
        target_agent = "eda"  # Use EDA for data analysis
    else:
        target_agent = "general"
    
    return {
        "task_plan": task_plan,
        "current_task": {
            **current_task,
            "enhanced_prompt": enhanced_prompt,
            "target_agent": target_agent
        },
        "sse_events": [{
            "event": "status", 
            "data": f"Executing: {current_task['name']} ({current_idx + 1}/{len(tasks)})"
        }]
    }


async def complete_task(state: AgentState) -> dict:
    """
    Mark current task as complete and store results.
    Updates task plan for next iteration.
    """
    task_plan = state.get("task_plan", {})
    current_task = state.get("current_task", {})
    task_result = state.get("task_result", {})
    
    if not current_task:
        return {"sse_events": [{"event": "error", "data": "No current task to complete"}]}
    
    task_id = current_task.get("id")
    
    # Mark as completed
    completed = task_plan.get("completed_tasks", [])
    if task_id not in completed:
        completed.append(task_id)
    
    # Store result
    results = task_plan.get("task_results", {})
    results[task_id] = {
        "output": task_result.get("output", ""),
        "type": task_result.get("type", "text"),
        "summary": task_result.get("summary", task_result.get("output", "")[:200])
    }
    
    task_plan["completed_tasks"] = completed
    task_plan["task_results"] = results
    task_plan["current_task_index"] = task_plan.get("current_task_index", 0) + 1
    
    # Check if all tasks done
    all_done = len(completed) >= len(task_plan.get("tasks", []))
    
    events = []
    if all_done:
        events.append({"event": "status", "data": "✓ All tasks completed! Compiling results..."})
    else:
        remaining = len(task_plan.get("tasks", [])) - len(completed)
        events.append({"event": "status", "data": f"✓ Task complete. {remaining} remaining"})
    
    return {
        "task_plan": task_plan,
        "current_task": None,
        "task_result": None,
        "all_tasks_complete": all_done,
        "sse_events": events
    }


async def compile_final_report(state: AgentState) -> dict:
    """
    Compile all task results into a final comprehensive report.
    """
    task_plan = state.get("task_plan", {})
    user_msg = state.get("user_message", "")
    task_results = task_plan.get("task_results", {})
    skill_used = task_plan.get("skill_used")
    
    # Build context from all results
    results_context = []
    for task_id, result in task_results.items():
        results_context.append(f"### {task_id}\n{result.get('output', 'No output')}")
    
    full_context = "\n\n".join(results_context)
    
    # Generate final report
    messages = [
        {"role": "system", "content": """You are a Report Compiler. Create a comprehensive, well-structured final report from multiple task results.

Structure your report as:
1. Executive Summary (2-3 sentences)
2. Key Findings (bullet points)
3. Detailed Analysis (organized by topic)
4. Visualizations/Charts (if any)
5. Recommendations/Next Steps

Make it professional, clear, and actionable."""},
        {"role": "user", "content": f"""User Request: {user_msg}

Task Results:
{full_context}

Skill Used: {skill_used or 'Custom plan'}

Generate a comprehensive final report."""}
    ]
    
    try:
        response = await _client.chat.completions.create(
            model=settings.llm_model_name,
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )
        
        final_report = response.choices[0].message.content.strip()
        
    except Exception as e:
        final_report = f"Report compilation failed: {str(e)}\n\nRaw Results:\n{full_context}"
    
    return {
        "result": {
            "type": "text",
            "data": {
                "content": final_report,
                "title": f"Analysis Report: {user_msg[:50]}..."
            }
        },
        "sse_events": [{"event": "status", "data": "✓ Report compiled successfully"}]
    }
