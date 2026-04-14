"""
Copilot service: LLM interaction, operation execution, and revert logic.
The copilot is strictly a FILE EDITOR — it never does analysis, charts, or code.
"""

import json
import copy
from typing import AsyncGenerator, Optional, Any

import pandas as pd
from openai import AsyncOpenAI

from config import settings
from models.schemas import Operation, CopilotRequest
from models.session import session_store
from services import file_service


# ── LLM Client ───────────────────────────────────────────────

_client = AsyncOpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
)

COPILOT_SYSTEM_PROMPT = """You are a spreadsheet file editor assistant called "Sheets Copilot". You help users modify their data files through natural language instructions.

## YOUR CAPABILITIES (you CAN do these):
- Answer questions about the data (e.g., "what is the average sales for Q3")
- Add a row with specified values
- Edit a specific cell or set of cells
- Delete rows matching a condition
- Add a derived/calculated column
- Rename a column
- Sort or filter data

## YOUR BOUNDARIES (you CANNOT do these — you MUST redirect):
- Generate charts, graphs, or any visualization
- Run Python code or scripts
- Perform EDA, correlations, statistical analysis, or machine learning
- Connect to a database
- Create pivot tables or complex aggregations that need code

When the user asks for something outside your scope, respond warmly and set "redirect" to true. Example:
"I can't create charts here, but Agent Chat is built exactly for that — it can generate interactive visualizations from your data."

## RESPONSE FORMAT
You MUST respond with valid JSON only. No markdown, no extra text.
{
  "reply": "Your conversational response to the user",
  "operation": null | {
    "type": "add_row" | "update_cell" | "update_cells_bulk" | "delete_rows" | "add_column" | "rename_column",
    "description": "Plain English label for the operation log, e.g. 'Added row · Raju · Oct · ₹52,000'",
    "params": { ... }
  },
  "redirect": false | true
}

## OPERATION PARAM SCHEMAS:
- add_row: {"values": {"col_name": "value", ...}}
- update_cell: {"row_index": 0, "column": "col_name", "value": "new_value"}
- update_cells_bulk: {"updates": [{"row_index": 0, "column": "col_name", "value": "new_value"}, ...]}
- delete_rows: {"condition_column": "col_name", "condition_value": "value"} OR {"row_indices": [0, 1, 2]}
- add_column: {"column_name": "new_col", "expression": "pandas expression string using df['col']", "description": "what this column represents"}
- rename_column: {"old_name": "current_name", "new_name": "desired_name"}

## IMPORTANT RULES:
1. Row indices are 0-based.
2. For add_column, the expression must be a valid pandas expression that can be eval'd with df as the DataFrame.
3. Always provide a human-readable "description" in the operation.
4. If the user just asks a question (no edit needed), set operation to null.
5. Never output anything outside the JSON format.
"""


def _build_data_context(df: pd.DataFrame) -> str:
    """Build a concise data context string for the LLM."""
    info_parts = []
    info_parts.append(f"**Shape:** {len(df)} rows × {len(df.columns)} columns")

    # Column info
    col_info = []
    for col in df.columns:
        dtype = file_service.infer_column_type(df[col])
        non_null = df[col].notna().sum()
        col_info.append(f"  - {col} ({dtype}, {non_null}/{len(df)} non-null)")
    info_parts.append("**Columns:**\n" + "\n".join(col_info))

    # Sample rows (head 15 + tail 15)
    sample = pd.concat([df.head(15), df.tail(15)]).drop_duplicates()
    info_parts.append(f"**Sample data (up to 30 rows):**\n{sample.to_string(max_rows=30)}")

    return "\n\n".join(info_parts)


# ── Operation Execution ──────────────────────────────────────


def execute_operation(df: pd.DataFrame, op_type: str, params: dict) -> tuple[pd.DataFrame, dict]:
    """
    Execute an operation on the DataFrame.
    Returns: (updated_df, inverse_data for revert)
    """
    inverse_data = {}

    if op_type == "add_row":
        values = params.get("values", {})
        new_index = len(df)
        new_row = pd.DataFrame([values])
        df = pd.concat([df, new_row], ignore_index=True)
        inverse_data = {"row_index": new_index}

    elif op_type == "update_cell":
        row_idx = params["row_index"]
        col = params["column"]
        new_val = params["value"]
        # Store original value
        original = df.at[row_idx, col]
        inverse_data = {"row_index": row_idx, "column": col, "original_value": _serialize_value(original)}
        df.at[row_idx, col] = new_val

    elif op_type == "update_cells_bulk":
        updates = params.get("updates", [])
        originals = []
        for u in updates:
            row_idx = u["row_index"]
            col = u["column"]
            original = df.at[row_idx, col]
            originals.append({"row_index": row_idx, "column": col, "original_value": _serialize_value(original)})
            df.at[row_idx, col] = u["value"]
        inverse_data = {"originals": originals}

    elif op_type == "delete_rows":
        if "row_indices" in params:
            indices = params["row_indices"]
        elif "condition_column" in params:
            col = params["condition_column"]
            val = params["condition_value"]
            indices = df[df[col].astype(str) == str(val)].index.tolist()
        else:
            indices = []

        # Store deleted rows for revert
        deleted_rows = df.loc[indices].to_dict(orient="records")
        inverse_data = {"deleted_rows": deleted_rows, "indices": indices}
        df = df.drop(indices).reset_index(drop=True)

    elif op_type == "add_column":
        col_name = params["column_name"]
        expression = params.get("expression", "None")
        try:
            df[col_name] = eval(expression, {"df": df, "pd": pd, "__builtins__": {}})
        except Exception as e:
            raise ValueError(f"Could not compute column: {str(e)}")
        inverse_data = {"column_name": col_name}

    elif op_type == "rename_column":
        old_name = params["old_name"]
        new_name = params["new_name"]
        df = df.rename(columns={old_name: new_name})
        inverse_data = {"old_name": old_name, "new_name": new_name}

    else:
        raise ValueError(f"Unknown operation type: {op_type}")

    return df, inverse_data


def _serialize_value(val) -> Any:
    """Convert Pandas values to JSON-serializable types."""
    if pd.isna(val):
        return None
    if hasattr(val, "item"):  # numpy scalar
        return val.item()
    return val


# ── Revert Logic ─────────────────────────────────────────────


def revert_operation(file_id: str, operation_id: str, session_id: str) -> dict:
    """
    Revert an operation by replaying all other operations from the original file.
    Returns the updated data for the frontend.
    """
    session = session_store.get(session_id)
    ops = session.operations_log

    # Find the operation index
    op_idx = None
    for i, op in enumerate(ops):
        if op.id == operation_id:
            op_idx = i
            break

    if op_idx is None:
        raise ValueError("Operation not found.")

    # Reload original file from disk
    df = file_service.load_dataframe(file_id)
    # Re-read from disk to get the original
    record = file_service.get_file_record(file_id)
    if not record:
        raise ValueError("File not found.")

    from pathlib import Path
    file_path = settings.upload_path / record.filename
    ext = Path(record.filename).suffix.lower()
    if ext == ".csv":
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path, engine="openpyxl")

    # Remove this operation and all after it
    removed_ops = ops[op_idx:]
    session.operations_log = ops[:op_idx]

    # Apply inverse operations from the end backwards
    df = session.dataframe.copy() if session.dataframe is not None else file_service.load_dataframe(file_id)

    for op in reversed(removed_ops):
        df = _apply_inverse(df, op)

    # Save the updated dataframe
    session.dataframe = df
    file_service.save_dataframe(file_id, df)

    rows = df.where(df.notna(), None).to_dict(orient="records")
    columns = [{"name": c, "dtype": file_service.infer_column_type(df[c])} for c in df.columns]

    return {
        "rows": rows,
        "columns": columns,
        "total_rows": len(df),
        "reverted_count": len(removed_ops),
    }


def _apply_inverse(df: pd.DataFrame, op: Operation) -> pd.DataFrame:
    """Apply the inverse of an operation to revert it."""
    inv = op.inverse_data

    if op.type == "add_row":
        idx = inv.get("row_index")
        if idx is not None and idx < len(df):
            df = df.drop(idx).reset_index(drop=True)

    elif op.type == "update_cell":
        df.at[inv["row_index"], inv["column"]] = inv["original_value"]

    elif op.type == "update_cells_bulk":
        for orig in inv.get("originals", []):
            df.at[orig["row_index"], orig["column"]] = orig["original_value"]

    elif op.type == "delete_rows":
        deleted = inv.get("deleted_rows", [])
        indices = inv.get("indices", [])
        if deleted:
            insert_df = pd.DataFrame(deleted)
            df = pd.concat([df, insert_df], ignore_index=True)

    elif op.type == "add_column":
        col = inv.get("column_name")
        if col and col in df.columns:
            df = df.drop(columns=[col])

    elif op.type == "rename_column":
        df = df.rename(columns={inv["new_name"]: inv["old_name"]})

    return df


# ── Streaming Chat ───────────────────────────────────────────


async def stream_chat(request: CopilotRequest) -> AsyncGenerator[dict, None]:
    """
    Stream copilot response via SSE.
    Yields dicts with event type and data.
    
    KEY FIX: We do NOT stream raw tokens to the user because the LLM
    returns JSON. Instead, we collect the full response, parse it,
    then send the clean reply text in one shot.
    """
    session = session_store.get(request.session_id)

    # Load DataFrame
    try:
        df = file_service.load_dataframe(request.file_id)
        session.dataframe = df
        session.file_id = request.file_id
    except ValueError as e:
        yield {"event": "error", "data": str(e)}
        return

    # Build context
    data_context = _build_data_context(df)

    # Build messages
    messages = [
        {"role": "system", "content": COPILOT_SYSTEM_PROMPT},
        {"role": "system", "content": f"## CURRENT DATA CONTEXT:\n{data_context}"},
    ]

    # Add conversation history (last 10 turns)
    history = session.agent_conversation_history[-20:]
    messages.extend(history)

    # Add current message
    messages.append({"role": "user", "content": request.message})

    # Show a thinking status while we wait for the LLM
    yield {"event": "status", "data": "Copilot is thinking..."}

    # Collect the full response (do NOT stream individual tokens)
    full_response = ""
    try:
        response = await _client.chat.completions.create(
            model=settings.llm_model_name,
            messages=messages,
            stream=False,  # No streaming — collect full JSON response
            temperature=0.1,
        )
        full_response = response.choices[0].message.content.strip()

    except Exception as e:
        yield {"event": "error", "data": "Something went wrong talking to the AI. Please try again."}
        return

    # Parse the full response as JSON
    try:
        json_str = full_response
        # Handle potential markdown code blocks
        if json_str.startswith("```"):
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
            json_str = json_str.strip()

        parsed = json.loads(json_str)
    except json.JSONDecodeError:
        # If JSON parsing fails, treat it as a plain text reply
        parsed = {"reply": full_response, "operation": None, "redirect": False}

    # Send the clean reply text as tokens (for the typing effect)
    reply_text = parsed.get("reply", full_response)
    # Send in chunks for a nice typing effect
    chunk_size = 8
    for i in range(0, len(reply_text), chunk_size):
        yield {"event": "token", "data": reply_text[i:i + chunk_size]}

    # Update conversation history
    session.agent_conversation_history.append({"role": "user", "content": request.message})
    session.agent_conversation_history.append({"role": "assistant", "content": full_response})

    # Handle operation if present
    if parsed.get("operation"):
        op_data = parsed["operation"]
        try:
            updated_df, inverse_data = execute_operation(
                df.copy(), op_data["type"], op_data.get("params", {})
            )

            # Create operation record
            operation = Operation(
                file_id=request.file_id,
                type=op_data["type"],
                description=op_data.get("description", op_data["type"]),
                params=op_data.get("params", {}),
                inverse_data=inverse_data,
            )

            # Save to session and disk
            session.operations_log.append(operation)
            session.dataframe = updated_df
            file_service.save_dataframe(request.file_id, updated_df)
            # Update cache
            file_service._dataframe_cache[request.file_id] = updated_df

            # Get updated rows for frontend
            rows = updated_df.where(updated_df.notna(), None).to_dict(orient="records")
            columns_info = [
                {"name": c, "dtype": file_service.infer_column_type(updated_df[c])}
                for c in updated_df.columns
            ]

            yield {
                "event": "operation",
                "data": {
                    "operation": operation.model_dump(mode="json"),
                    "rows": rows,
                    "columns": columns_info,
                    "total_rows": len(updated_df),
                },
            }

        except Exception as e:
            yield {"event": "error", "data": f"Could not apply the edit: {str(e)}"}

    # Handle redirect
    if parsed.get("redirect"):
        yield {"event": "redirect", "data": {"file_id": request.file_id}}

    yield {"event": "done", "data": ""}
