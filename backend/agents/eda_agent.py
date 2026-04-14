"""
EDA Agent: runs a comprehensive Pandas profiling pipeline.
Produces structured JSON for the EDA Report card.
"""

import json
import numpy as np
import pandas as pd
from openai import AsyncOpenAI
from config import settings
from agents.state import AgentState


_client = AsyncOpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
)


async def eda_agent_node(state: AgentState) -> dict:
    """Run EDA pipeline and return structured report."""
    events = []
    events.append({"event": "status", "data": "Profiling data..."})

    df = state.get("dataframe")
    if df is None:
        return {
            "sse_events": [{"event": "error", "data": "No data loaded for analysis."}],
            "result": None,
        }

    # ── Basic Info ──
    shape = {"rows": len(df), "cols": len(df.columns)}
    dtypes = {col: str(df[col].dtype) for col in df.columns}

    # ── Missing Values ──
    missing = {}
    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        missing[col] = {
            "count": null_count,
            "percentage": round(null_count / len(df) * 100, 1) if len(df) > 0 else 0,
        }

    events.append({"event": "status", "data": "Computing statistics..."})

    # ── Descriptive Stats ──
    numeric_df = df.select_dtypes(include="number")
    stats = {}
    if len(numeric_df.columns) > 0:
        desc = numeric_df.describe().to_dict()
        for col, col_stats in desc.items():
            stats[col] = {k: round(float(v), 4) if pd.notna(v) else None for k, v in col_stats.items()}

    # ── Correlations ──
    events.append({"event": "status", "data": "Running correlation analysis..."})
    correlations = []
    if len(numeric_df.columns) >= 2:
        try:
            corr_matrix = numeric_df.corr()
            # Get top correlations (excluding self-correlation)
            pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    val = corr_matrix.iloc[i, j]
                    if pd.notna(val):
                        pairs.append({"col1": col1, "col2": col2, "value": round(float(val), 4)})

            pairs.sort(key=lambda x: abs(x["value"]), reverse=True)
            correlations = pairs[:10]  # Top 10
        except Exception:
            pass

    # ── Outliers (IQR method) ──
    events.append({"event": "status", "data": "Detecting outliers..."})
    outliers = {}
    for col in numeric_df.columns:
        try:
            q1 = numeric_df[col].quantile(0.25)
            q3 = numeric_df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outlier_count = int(((numeric_df[col] < lower) | (numeric_df[col] > upper)).sum())
            outliers[col] = outlier_count
        except Exception:
            outliers[col] = 0

    # ── Column Types Summary ──
    type_summary = {}
    for col in df.columns:
        from services.file_service import infer_column_type
        type_summary[col] = infer_column_type(df[col])

    # ── Build EDA Report ──
    eda_report = {
        "shape": shape,
        "dtypes": dtypes,
        "type_summary": type_summary,
        "missing": missing,
        "statistics": stats,
        "correlations": correlations,
        "outliers": outliers,
    }

    # ── Generate Summary with LLM ──
    events.append({"event": "status", "data": "Writing analysis summary..."})
    summary_text = ""
    try:
        summary_prompt = f"""You are a data analyst. Based on this EDA report, write a concise 3-5 sentence summary highlighting the most interesting and actionable findings. Be specific about column names, values, and patterns.

## DATASET OVERVIEW:
- Shape: {shape['rows']} rows × {shape['cols']} columns
- Columns: {list(df.columns)}

## DATA QUALITY ISSUES (highlight these if present):
{json.dumps({k: v for k, v in missing.items() if v['percentage'] > 5}, default=str)}

## KEY STATISTICS (numeric columns only):
{json.dumps(stats, default=str)}

## TOP CORRELATIONS (absolute value > 0.5):
{json.dumps([c for c in correlations[:5] if abs(c['value']) > 0.5], default=str) or "No strong correlations found"}

## OUTLIER DETECTION (columns with >10% outliers):
{json.dumps({k: v for k, v in outliers.items() if v > len(df) * 0.1}, default=str) or "No significant outliers"}

## INSTRUCTIONS:
1. Start with the dataset shape and purpose
2. Highlight any data quality issues (missing values, anomalies)
3. Mention the strongest correlations and what they might mean
4. Point out notable outliers or unusual distributions
5. Suggest 1-2 potential next steps for analysis

Write in clear, professional language. Be specific with numbers and column names."""

        response = await _client.chat.completions.create(
            model=settings.llm_model_name,
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.3,
            max_tokens=400,
        )
        summary_text = response.choices[0].message.content.strip()
    except Exception:
        summary_text = f"Dataset contains {shape['rows']} rows and {shape['cols']} columns."

    eda_report["summary"] = summary_text

    # ── Emit Events ──
    events.append({"event": "eda", "data": json.dumps(eda_report, default=str)})
    events.append({"event": "text", "data": json.dumps({
        "agent_name": "EDA Agent",
        "content": summary_text,
    })})

    return {
        "sse_events": events,
        "result": {"type": "eda", "data": eda_report},
    }
