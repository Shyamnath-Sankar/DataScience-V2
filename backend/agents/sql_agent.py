"""
SQL Agent: Uses Vanna AI for NL→SQL, executes via SQLAlchemy.
Only active when source_type is "database".
"""

import json
import pandas as pd
from agents.state import AgentState


async def sql_agent_node(state: AgentState) -> dict:
    """Convert natural language to SQL, execute, and return results."""
    events = []
    events.append({"event": "status", "data": "Generating SQL query..."})

    db_engine = state.get("db_engine")
    if db_engine is None:
        return {
            "sse_events": [{"event": "error", "data": "No database connection. Please connect a database first."}],
            "result": None,
        }

    # Import here to avoid errors when Vanna isn't configured
    try:
        from services.database_service import vanna_instance
    except ImportError:
        return {
            "sse_events": [{"event": "error", "data": "Database service not available."}],
            "result": None,
        }

    try:
        # Generate SQL using Vanna
        sql = vanna_instance.generate_sql(state["user_message"])
        if not sql:
            events.append({"event": "error", "data": "Could not generate a SQL query from your question. Try rephrasing."})
            return {"sse_events": events, "result": None}

        events.append({"event": "status", "data": f"Executing query..."})

        # Execute the SQL
        result_df = pd.read_sql_query(sql, db_engine)

        sql_output = {
            "sql": sql,
            "columns": list(result_df.columns),
            "rows": result_df.head(200).where(result_df.head(200).notna(), None).to_dict(orient="records"),
            "total_rows": len(result_df),
        }

        events.append({"event": "sql_output", "data": json.dumps(sql_output, default=str)})
        events.append({"event": "text", "data": json.dumps({
            "agent_name": "SQL Agent",
            "content": f"Executed SQL query and returned {len(result_df)} rows.",
        })})

        return {
            "sse_events": events,
            "result": {"type": "sql_output", "data": sql_output},
        }

    except Exception as e:
        error_msg = str(e)
        if "syntax" in error_msg.lower():
            events.append({"event": "error", "data": "The generated SQL had a syntax error. Try rephrasing your question."})
        else:
            events.append({"event": "error", "data": "Something went wrong running the SQL query. Try a different question."})
        return {"sse_events": events, "result": None}
