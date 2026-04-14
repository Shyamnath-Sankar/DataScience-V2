"""
Visualizer Agent: uses LLM to choose chart type and generate Plotly JSON spec.
"""

import json
from openai import AsyncOpenAI
from config import settings
from agents.state import AgentState


_client = AsyncOpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
)

VIZ_SYSTEM_PROMPT = """You are a data visualization expert. Given a user's request and dataset information, generate an interactive Plotly chart specification.

## CHART TYPE DECISION LOGIC:
- Time/date column + numeric → Line chart
- Categorical + numeric → Bar chart
- Two numeric columns → Scatter plot
- Single numeric column distribution → Histogram or Box plot
- Correlation matrix → Heatmap
- Multiple categories + values → Grouped bar or Stacked bar
- Proportions/parts of whole → Pie/Donut chart

## RESPONSE FORMAT (JSON only, no markdown):
{
  "chart_type": "line|bar|scatter|histogram|box|heatmap|pie",
  "title": "Clear descriptive title",
  "subtitle": "One-line explanation of what the chart shows",
  "plotly_data": [ ... ],
  "plotly_layout": {
    "template": "plotly_dark",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(24,24,27,1)",
    "font": {"family": "DM Sans, sans-serif", "color": "#fafafa"},
    "xaxis": {"title": "...", "gridcolor": "#27272a"},
    "yaxis": {"title": "...", "gridcolor": "#27272a"},
    ...any other layout properties
  }
}

## STYLING RULES:
- Use these colors for traces: ["#7c3aed", "#14b8a6", "#f59e0b", "#ef4444", "#3b82f6", "#ec4899", "#8b5cf6", "#06b6d4"]
- All backgrounds transparent or dark (#18181b)
- Grid lines subtle (#27272a)
- Font: DM Sans for labels, white/light text
- Make charts look premium and clean

## IMPORTANT:
- The plotly_data should be a list of trace objects compatible with Plotly.js
- Use actual column names from the data
- If you need to aggregate, specify the aggregation in the trace (e.g., histfunc)
- Respond ONLY with valid JSON"""


async def visualizer_agent_node(state: AgentState) -> dict:
    """Generate a Plotly chart specification."""
    events = []
    events.append({"event": "status", "data": "Analyzing data for visualization..."})

    df = state.get("dataframe")
    summary = state.get("dataframe_summary", {})

    if df is None:
        return {
            "sse_events": [{"event": "error", "data": "No data loaded for visualization."}],
            "result": None,
        }

    # Build data context for LLM
    sample_data = df.head(10).to_dict(orient="records")

    context = f"""Dataset columns: {list(df.columns)}
Column types: {json.dumps(summary.get('dtypes', {}), default=str)}
Shape: {len(df)} rows × {len(df.columns)} columns
Sample data (first 10 rows): {json.dumps(sample_data, default=str)}"""

    events.append({"event": "status", "data": "Generating chart specification..."})

    messages = [
        {"role": "system", "content": VIZ_SYSTEM_PROMPT},
        {"role": "user", "content": f"Data context:\n{context}\n\nUser request: {state['user_message']}"},
    ]

    try:
        response = await _client.chat.completions.create(
            model=settings.llm_model_name,
            messages=messages,
            temperature=0.2,
            max_tokens=2000,
        )

        raw = response.choices[0].message.content.strip()
        # Clean markdown
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        chart_spec = json.loads(raw)

        # Now we need to fill in actual data from the dataframe
        # The LLM generates a spec with column references — we evaluate them
        plotly_data = chart_spec.get("plotly_data", [])

        # Process each trace to inject actual data
        for trace in plotly_data:
            for axis in ["x", "y", "values", "labels", "z"]:
                if axis in trace and isinstance(trace[axis], str) and trace[axis] in df.columns:
                    trace[axis] = df[trace[axis]].dropna().tolist()

        chart_output = {
            "chart_type": chart_spec.get("chart_type", "bar"),
            "title": chart_spec.get("title", "Chart"),
            "subtitle": chart_spec.get("subtitle", ""),
            "plotly_data": plotly_data,
            "plotly_layout": chart_spec.get("plotly_layout", {}),
        }

        events.append({"event": "chart", "data": json.dumps(chart_output, default=str)})
        events.append({"event": "text", "data": json.dumps({
            "agent_name": "Visualizer Agent",
            "content": f"Here's a {chart_output['chart_type']} chart: {chart_output['subtitle']}",
        })})

        return {
            "sse_events": events,
            "result": {"type": "chart", "data": chart_output},
        }

    except json.JSONDecodeError:
        events.append({"event": "error", "data": "Failed to generate chart. Try rephrasing your request."})
        return {"sse_events": events, "result": None}
    except Exception as e:
        events.append({"event": "error", "data": "Something went wrong creating the visualization. Try again."})
        return {"sse_events": events, "result": None}
