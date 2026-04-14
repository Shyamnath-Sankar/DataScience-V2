"""
General Agent: conversational fallback for questions that don't need tools.
"""

import json
from openai import AsyncOpenAI
from config import settings
from agents.state import AgentState


_client = AsyncOpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
)


async def general_agent_node(state: AgentState) -> dict:
    """Answer general questions using LLM with data context and conversation history."""
    events = []
    events.append({"event": "status", "data": "Thinking..."})

    summary = state.get("dataframe_summary", {})
    history = state.get("conversation_history", [])
    result_context = state.get("result", None)
    
    # Build rich context including recent canvas outputs
    context_parts = []
    if summary:
        context_parts.append(f"Dataset: {summary.get('shape', {})} - Columns: {summary.get('columns', [])}")
    
    # Include previous analysis results for continuity
    if result_context:
        if isinstance(result_context, dict):
            if result_context.get("type") == "eda":
                context_parts.append(f"Recent EDA completed. Summary: {result_context.get('data', {}).get('summary', '')[:200]}...")
            elif result_context.get("type") == "code_output":
                context_parts.append(f"Recent code executed successfully.")
            elif result_context.get("type") == "chart":
                context_parts.append(f"Recent chart generated: {result_context.get('data', {}).get('title', '')}")

    messages = [
        {
            "role": "system",
            "content": f"""You are a helpful data science assistant. You answer questions about the user's dataset, 
explain concepts, suggest analyses, and provide guidance.

## CURRENT CONTEXT:
{" | ".join(context_parts) if context_parts else "No specific data context available."}

## IMPORTANT RULES:
1. Be concise, precise, and helpful. Use the data summary to give specific, relevant answers.
2. Do NOT write Python code or code snippets — you are NOT a code executor. If the user wants code executed, tell them to ask for it directly (e.g., "Try asking: 'Show the top 10 countries by population'").
3. Do NOT suggest charts or visualizations with code. Instead say something like "Try asking: 'Plot a bar chart of population by continent'" — the system will automatically generate and render it.
4. You CAN answer factual questions about the data using the summary provided (e.g., column names, types, sample values).
5. Keep responses short and actionable — 2-4 sentences max.
6. Reference previous analysis results when relevant to maintain conversation flow.""",
        },
    ]

    # Add conversation history (last 10 turns)
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": state["user_message"]})

    try:
        response = await _client.chat.completions.create(
            model=settings.llm_model_name,
            messages=messages,
            temperature=0.4,
            max_tokens=500,
        )
        reply = response.choices[0].message.content.strip()

        events.append({"event": "text", "data": json.dumps({
            "agent_name": "Assistant",
            "content": reply,
        })})

        return {
            "sse_events": events,
            "result": {"type": "text", "data": {"content": reply}},
        }

    except Exception:
        events.append({"event": "error", "data": "Something went wrong. Please try again."})
        return {"sse_events": events, "result": None}
