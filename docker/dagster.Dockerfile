FROM python:3.11-slim

WORKDIR /app

COPY ingestion/ ./ingestion/
COPY dagster_project/ ./dagster_project/
COPY dbt_project/ ./dbt_project/

RUN pip install --no-cache-dir -e ./ingestion -e ./dagster_project \
    && cd dbt_project && dbt deps --profiles-dir .

# DAGSTER_HOME kept separate from the project source and from data/, since
# it's Dagster's own run/event metadata (local SQLite backend), not pipeline
# data or application code.
RUN mkdir -p /app/dagster_home \
    && cp /app/dagster_project/dagster.yaml /app/dagster_home/dagster.yaml

ENV DAGSTER_HOME=/app/dagster_home \
    DBT_PROFILES_DIR=/app/dbt_project \
    PYTHONUNBUFFERED=1

WORKDIR /app/dagster_project
