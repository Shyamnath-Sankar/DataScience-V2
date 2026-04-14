"""
File service: upload, parse, store, list, delete, preview.
Handles CSV and XLSX files with Pandas.
"""

import uuid
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from fastapi import UploadFile

from config import settings
from models.schemas import FileRecord, ColumnInfo, FilePreview


# In-memory file registry
_file_registry: dict[str, FileRecord] = {}
_dataframe_cache: dict[str, pd.DataFrame] = {}


def infer_column_type(series: pd.Series) -> str:
    """Classify a Pandas Series as number/text/date/boolean."""
    dtype = series.dtype

    if pd.api.types.is_bool_dtype(dtype):
        return "boolean"
    if pd.api.types.is_numeric_dtype(dtype):
        return "number"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "date"

    # Try parsing as date
    if dtype == object:
        sample = series.dropna().head(20)
        if len(sample) > 0:
            try:
                pd.to_datetime(sample, infer_datetime_format=True)
                return "date"
            except (ValueError, TypeError):
                pass

    return "text"


def _build_column_info(df: pd.DataFrame) -> list[ColumnInfo]:
    """Build column metadata from a DataFrame."""
    columns = []
    for col in df.columns:
        dtype = infer_column_type(df[col])
        sample_vals = df[col].dropna().head(5).astype(str).tolist()
        columns.append(ColumnInfo(name=str(col), dtype=dtype, sample_values=sample_vals))
    return columns


async def upload_file(file: UploadFile) -> FileRecord:
    """Parse and store an uploaded file."""
    # Validate extension
    original_name = file.filename or "unknown"
    ext = Path(original_name).suffix.lower()
    if ext not in (".csv", ".xlsx"):
        raise ValueError("Only .csv and .xlsx files are supported.")

    # Read content
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise ValueError(f"File exceeds {settings.max_file_size_mb}MB limit.")

    # Generate unique filename
    file_id = str(uuid.uuid4())
    stored_name = f"{file_id}{ext}"
    file_path = settings.upload_path / stored_name

    # Save to disk
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse with Pandas
    try:
        if ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path, engine="openpyxl")
    except Exception as e:
        # Clean up on parse failure
        file_path.unlink(missing_ok=True)
        raise ValueError(f"This file couldn't be read. Make sure it's a valid {ext} file.")

    # Build metadata
    columns = _build_column_info(df)
    record = FileRecord(
        id=file_id,
        filename=stored_name,
        original_name=original_name,
        row_count=len(df),
        col_count=len(df.columns),
        columns=columns,
        file_size=len(content),
    )

    # Store in registry + cache
    _file_registry[file_id] = record
    _dataframe_cache[file_id] = df

    return record


def list_files() -> list[FileRecord]:
    """Return all uploaded file records."""
    return list(_file_registry.values())


def get_file_record(file_id: str) -> Optional[FileRecord]:
    """Get a single file record."""
    return _file_registry.get(file_id)


def delete_file(file_id: str) -> bool:
    """Delete a file from disk and memory."""
    record = _file_registry.pop(file_id, None)
    _dataframe_cache.pop(file_id, None)
    if record:
        file_path = settings.upload_path / record.filename
        file_path.unlink(missing_ok=True)
        return True
    return False


def load_dataframe(file_id: str) -> pd.DataFrame:
    """Load DataFrame from cache or disk."""
    if file_id in _dataframe_cache:
        return _dataframe_cache[file_id]

    record = _file_registry.get(file_id)
    if not record:
        raise ValueError("File not found.")

    file_path = settings.upload_path / record.filename
    ext = Path(record.filename).suffix.lower()

    if ext == ".csv":
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path, engine="openpyxl")

    _dataframe_cache[file_id] = df
    return df


def load_preview(file_id: str, max_rows: int = 200) -> FilePreview:
    """Load first N rows for grid display."""
    df = load_dataframe(file_id)
    record = _file_registry.get(file_id)
    if not record:
        raise ValueError("File not found.")

    preview_df = df.head(max_rows)
    # Convert to list of dicts, handling NaN
    rows = preview_df.where(preview_df.notna(), None).to_dict(orient="records")

    return FilePreview(
        file_id=file_id,
        columns=record.columns,
        rows=rows,
        total_rows=record.row_count,
        total_cols=record.col_count,
    )


def load_full_data(file_id: str) -> dict:
    """Load full file data as JSON."""
    df = load_dataframe(file_id)
    record = _file_registry.get(file_id)
    if not record:
        raise ValueError("File not found.")

    rows = df.where(df.notna(), None).to_dict(orient="records")
    return {
        "file_id": file_id,
        "columns": [c.model_dump() for c in record.columns],
        "rows": rows,
        "total_rows": record.row_count,
        "total_cols": record.col_count,
    }


def save_dataframe(file_id: str, df: pd.DataFrame):
    """Save updated DataFrame back to disk and update metadata."""
    record = _file_registry.get(file_id)
    if not record:
        raise ValueError("File not found.")

    file_path = settings.upload_path / record.filename
    ext = Path(record.filename).suffix.lower()

    if ext == ".csv":
        df.to_csv(file_path, index=False)
    else:
        df.to_excel(file_path, index=False, engine="openpyxl")

    # Update cache and metadata
    _dataframe_cache[file_id] = df
    record.row_count = len(df)
    record.col_count = len(df.columns)
    record.columns = _build_column_info(df)


def cleanup_old_files():
    """Delete files older than 24 hours."""
    cutoff = datetime.utcnow() - timedelta(hours=settings.session_ttl_hours)
    to_delete = [
        fid for fid, rec in _file_registry.items()
        if rec.uploaded_at < cutoff
    ]
    for fid in to_delete:
        delete_file(fid)
    return len(to_delete)
