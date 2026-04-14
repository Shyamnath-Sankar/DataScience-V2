"""
Orchestrator node: classifies user intent and routes to the correct agent.
"""

import json
from openai import AsyncOpenAI
from config import settings
from agents.state import AgentState


_client = AsyncOpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
)

CLASSIFICATION_PROMPT = """You are an intent classifier for a data science AI assistant. Given a user's question, classify the intent into exactly one category.

## CATEGORIES:
- eda: Exploratory data analysis — data profiling, statistics, missing values, correlations, outliers, describe, summary, data quality, column distributions, shape, info, dtypes, nunique.
- visualization: Any chart, graph, plot, visual, or diagram. Keywords: plot, chart, graph, bar, line, scatter, histogram, pie, heatmap, show me, visualize, distribution plot.
- code: Custom Python code, calculations, transformations, data manipulation, filtering, grouping, aggregations, sorting, creating new columns, complex computations, top N, ranking, comparisons.
- sql: SQL queries or natural-language-to-SQL. ONLY when the source is a database.
- general: Greetings, explanations, definitions, how-to questions that don't need data, or meta questions.

## KEY RULES:
- If the user asks to "show", "find", "list", "get", "compute", "calculate", "top", "bottom", "filter", "sort", or "count" → classify as "code"
- If the user asks to "plot", "chart", "graph", "visualize", or "draw" → classify as "visualization"  
- If the user asks about "statistics", "summary", "profile", "describe", "missing", "correlation", "outlier" → classify as "eda"
- When in doubt between "general" and "code", prefer "code" — it's better to execute code than just talk about it
- When in doubt between "general" and "visualization", prefer "visualization"

Respond with ONLY the category name, nothing else. No quotes, no explanation, no punctuation."""


async def orchestrator_node(state: AgentState) -> dict:
    """Classify intent and route to the correct agent."""

    # If a mode is pinned, skip classification
    if state.get("pinned_mode"):
        intent = state["pinned_mode"]
        return {
            "classified_intent": intent,
            "sse_events": [{"event": "status", "data": f"Using {intent} agent..."}],
        }

    # Use LLM to classify with rich context
    df = state.get("dataframe")
    summary = state.get("dataframe_summary", {})
    user_msg = state["user_message"]
    
    # Build rich data context for better classification
    if df is not None:
        sample_data = df.head(5).to_dict(orient="records")
        numeric_cols = [col for col, dtype in summary.get('dtypes', {}).items() 
                       if 'int' in str(dtype) or 'float' in str(dtype)]
        date_cols = [col for col, dtype in summary.get('dtypes', {}).items() 
                    if 'datetime' in str(dtype) or 'object' in str(dtype)]
        data_context = f"""Dataset shape: {len(df)} rows × {len(df.columns)} columns
Columns: {list(df.columns)}
Column types: {json.dumps(summary.get('dtypes', {}), default=str)}
Numeric columns: {numeric_cols}
Date/time columns: {date_cols}
Sample data (first 5 rows): {json.dumps(sample_data, default=str)}"""
    else:
        data_context = f"Columns: {summary.get('columns', [])}"

    messages = [
        {"role": "system", "content": CLASSIFICATION_PROMPT},
        {"role": "user", "content": f"{data_context}\n\nUser question: {user_msg}"},
    ]

    try:
        response = await _client.chat.completions.create(
            model=settings.llm_model_name,
            messages=messages,
            temperature=0,
            max_tokens=10,
        )
        raw_intent = response.choices[0].message.content.strip().lower()
        
        # Clean up — sometimes the LLM adds quotes or punctuation
        intent = raw_intent.replace('"', '').replace("'", "").replace(".", "").strip()

        # Validate
        valid_intents = {"eda", "visualization", "code", "sql", "general"}
        if intent not in valid_intents:
            # Fallback heuristics based on keywords
            intent = _keyword_fallback(user_msg)

        # Don't route to SQL if source is file
        if intent == "sql" and state.get("source_type") != "database":
            intent = "code"  # Fallback to code for file-based queries

    except Exception:
        intent = _keyword_fallback(user_msg)

    agent_names = {
        "eda": "EDA Agent",
        "visualization": "Visualizer Agent",
        "code": "Code Executor",
        "sql": "SQL Agent",
        "general": "Assistant",
    }

    return {
        "classified_intent": intent,
        "sse_events": [{"event": "status", "data": f"Routing to {agent_names.get(intent, intent)}..."}],
    }


def _keyword_fallback(msg: str) -> str:
    """Simple keyword-based fallback classifier."""
    msg_lower = msg.lower()
    
    viz_keywords = ["plot", "chart", "graph", "visualiz", "diagram", "draw", "bar chart", "line chart", "scatter", "histogram", "pie", "heatmap"]
    eda_keywords = ["eda", "profile", "descri", "statistic", "missing", "correlat", "outlier", "summary", "null", "info", "dtype"]
    code_keywords = ["top", "bottom", "filter", "sort", "group", "count", "average", "mean", "sum", "max", "min", "calculate", "compute", "find", "list", "show me", "get", "how many", "which", "what is the", "largest", "smallest", "most", "least"]
    
    for kw in viz_keywords:
        if kw in msg_lower:
            return "visualization"
    for kw in eda_keywords:
        if kw in msg_lower:
            return "eda"
    for kw in code_keywords:
        if kw in msg_lower:
            return "code"
    
    return "general"
