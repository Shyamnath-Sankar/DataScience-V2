"""
Database service: SQLAlchemy connections and Vanna AI for NL→SQL.
Uses local ChromaDB as the vector store.
"""

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from typing import Optional

from config import settings


# ── Vanna Setup (Local ChromaDB + OpenAI-compatible LLM) ─────


class DataSciVanna:
    """
    Wrapper around Vanna AI with local ChromaDB vector store.
    Lazy-initialized to avoid import errors if Vanna isn't configured.
    """

    def __init__(self):
        self._vn = None
        self._initialized = False

    def _init_vanna(self):
        """Initialize Vanna with ChromaDB + OpenAI."""
        if self._initialized:
            return

        try:
            from vanna.openai import OpenAI_Chat
            from vanna.chromadb import ChromaDB_VectorStore

            class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
                def __init__(self, config=None):
                    ChromaDB_VectorStore.__init__(self, config=config)
                    OpenAI_Chat.__init__(self, config=config)

            self._vn = MyVanna(config={
                "api_key": settings.llm_api_key,
                "model": settings.llm_model_name,
                "base_url": settings.llm_base_url,
            })
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Vanna: {str(e)}")

    def train_on_schema(self, engine):
        """Train Vanna on the database schema."""
        self._init_vanna()
        inspector = inspect(engine)
        schemas = inspector.get_schema_names()

        for schema in schemas:
            if schema in ("information_schema", "pg_catalog"):
                continue
            tables = inspector.get_table_names(schema=schema)
            for table in tables:
                try:
                    columns = inspector.get_columns(table, schema=schema)
                    ddl_parts = []
                    for col in columns:
                        ddl_parts.append(f"  {col['name']} {col['type']}")
                    ddl = f"CREATE TABLE {schema}.{table} (\n" + ",\n".join(ddl_parts) + "\n);"
                    self._vn.train(ddl=ddl)
                except Exception:
                    continue

    def generate_sql(self, question: str) -> Optional[str]:
        """Generate SQL from natural language."""
        self._init_vanna()
        try:
            sql = self._vn.generate_sql(question)
            return sql
        except Exception:
            return None


# Global Vanna instance
vanna_instance = DataSciVanna()


# ── Database Connection ──────────────────────────────────────


def connect_database(connection_url: str) -> dict:
    """
    Connect to a database and return table list.
    Supports PostgreSQL URLs and SQLite file paths.
    """
    try:
        engine = create_engine(connection_url)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Get table list
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        return {
            "engine": engine,
            "tables": tables,
            "success": True,
        }
    except Exception as e:
        raise ValueError(f"Could not connect to database: {str(e)}")


def train_vanna_on_db(engine) -> bool:
    """Train Vanna on the database schema."""
    try:
        vanna_instance.train_on_schema(engine)
        return True
    except Exception as e:
        raise ValueError(f"Failed to train on schema: {str(e)}")


def execute_sql(engine, sql: str) -> pd.DataFrame:
    """Execute SQL and return results as DataFrame."""
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text(sql), conn)
        return df
    except Exception as e:
        raise ValueError(f"SQL execution failed: {str(e)}")
