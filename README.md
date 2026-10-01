# SEPTA Bus Lateness Pipeline

Local medallion ETL pipeline + dashboard for SEPTA bus/trolley lateness, built on
Dagster, dbt (dbt-duckdb), DuckDB, and Streamlit.

## Run it

```
cp .env.example .env
docker compose up --build
```

- Dagit (orchestration UI): http://localhost:3000
- Dashboard: http://localhost:8501

The `*/5 * * * *` schedule starts polling `TransitViewAll` once the daemon is
up. The GTFS and Stops-API reference data refresh weekly/daily respectively
and need at least one manual run to populate `dim_stop`/`dim_route_shape`
before their first scheduled tick - from Dagit: Jobs -> `gtfs_refresh_job` /
`stops_refresh_job` -> Launch Run.

## Local development (without Docker)

```
python -m venv .venv
.venv/Scripts/pip install -e ./ingestion -e ./dagster_project
cd dbt_project && ../.venv/Scripts/dbt deps
```

Run a single poll + dbt build manually:

```
cd dagster_project
RAW_DATA_PATH=../data/raw DUCKDB_PATH=../data/duckdb/septa.duckdb DAGSTER_HOME=. \
  dagster job execute -m septa_dagster.definitions -j poll_and_transform_job
```

Run the dashboard against that data:

```
cd streamlit_app
DUCKDB_PATH=../data/duckdb/septa.duckdb ../.venv/Scripts/streamlit run app.py
```

## Tests

```
cd ingestion && ../.venv/Scripts/pytest
```
