import os
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

DEFAULT_DUCKDB_PATH = "/app/data/duckdb/septa.duckdb"


def _duckdb_path() -> str:
    return os.environ.get("DUCKDB_PATH", DEFAULT_DUCKDB_PATH)


def require_database():
    """Shows a friendly message and halts the page if the pipeline hasn't
    landed a DuckDB file yet (e.g. right after `docker compose up` before
    the first 5-minute poll has run)."""
    if not Path(_duckdb_path()).exists():
        st.info("No data yet - waiting for the pipeline's first poll cycle to run.")
        st.stop()


def query(sql: str, params: list | None = None) -> pd.DataFrame:
    """Opens a fresh read-only connection per query rather than holding one
    for the app's lifetime, so a long-lived connection never pins a stale
    snapshot while dagster-daemon is the sole read-write connection.
    """
    con = duckdb.connect(_duckdb_path(), read_only=True)
    try:
        return con.execute(sql, params or []).fetch_df()
    finally:
        con.close()
