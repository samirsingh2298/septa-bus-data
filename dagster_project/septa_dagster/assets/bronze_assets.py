import gzip
import json
import random
import time
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import duckdb
from dagster import AssetExecutionContext, AssetOut, MetadataValue, Output, RetryPolicy, asset, multi_asset
from septa_client.normalize import normalize_stops_by_route, normalize_transitview_all

from ..paths import raw_data_path
from ..resources import SeptaApiResource

# dbt only declares sources for routes/shapes/trips (what dim_route,
# dim_route_shape need); stops.txt/stop_times.txt are still landed to disk
# for completeness/future use but have no dbt source or Dagster asset output.
GTFS_FILES_TO_EXTRACT = ("routes.txt", "stops.txt", "trips.txt", "stop_times.txt", "shapes.txt")
GTFS_DBT_SOURCE_FILES = {
    "raw_gtfs_routes": "routes.txt",
    "raw_gtfs_shapes": "shapes.txt",
    "raw_gtfs_trips": "trips.txt",
}


@asset(group_name="bronze", retry_policy=RetryPolicy(max_retries=2, delay=30))
def raw_transitview_all_snapshot(context: AssetExecutionContext, septa_api: SeptaApiResource) -> None:
    """One HTTP call per tick: every active bus/trolley across every route.

    Landed as a flat JSON array (one record per vehicle) rather than the raw
    nested API payload, so downstream dbt staging never has to guess at an
    undocumented response shape - see ingestion/septa_client/normalize.py.
    """
    ingested_at = datetime.now(timezone.utc)
    source_url = f"{septa_api.base_url}/api/TransitViewAll/"

    with septa_api.get_client() as client:
        payload = client.get_transitview_all()

    records = normalize_transitview_all(payload)
    for record in records:
        record["ingested_at"] = ingested_at.isoformat()
        record["source_url"] = source_url

    routes_seen = {r["route_id"] for r in records if r["route_id"]}

    out_dir = Path(raw_data_path()) / "transitview_all" / f"dt={ingested_at:%Y-%m-%d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{ingested_at:%Y%m%dT%H%M%SZ}.json.gz"

    with gzip.open(out_path, "wt", encoding="utf-8") as f:
        json.dump(records, f)

    context.add_output_metadata(
        {
            "vehicle_count": len(records),
            "route_count": len(routes_seen),
            "output_file": MetadataValue.path(str(out_path)),
        }
    )


@multi_asset(
    group_name="bronze",
    outs={name: AssetOut() for name in GTFS_DBT_SOURCE_FILES},
    retry_policy=RetryPolicy(max_retries=2, delay=60),
)
def raw_gtfs_snapshot(context: AssetExecutionContext, septa_api: SeptaApiResource):
    """Weekly pull of SEPTA's static GTFS feed: route/stop reference data and
    route polyline geometry for the map, for scheduled routes.

    gtfs_public.zip is a zip-of-zips (confirmed live): it contains
    google_bus.zip and google_rail.zip, each a normal GTFS feed. We only need
    the bus feed. One Dagster asset output per dbt source file so each maps
    to a distinct asset key (Dagster requires unique keys per dbt resource).
    """
    with septa_api.get_client() as client:
        outer_zip_bytes = client.get_gtfs_feed_bytes()

    dt_folder = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = Path(raw_data_path()) / "gtfs" / f"dt={dt_folder}"
    out_dir.mkdir(parents=True, exist_ok=True)

    extracted = []
    with zipfile.ZipFile(BytesIO(outer_zip_bytes)) as outer_zf:
        inner_bytes = outer_zf.read("google_bus.zip")

    with zipfile.ZipFile(BytesIO(inner_bytes)) as inner_zf:
        names = set(inner_zf.namelist())
        for filename in GTFS_FILES_TO_EXTRACT:
            if filename in names:
                inner_zf.extract(filename, out_dir)
                extracted.append(filename)

    for asset_name, filename in GTFS_DBT_SOURCE_FILES.items():
        yield Output(
            None,
            output_name=asset_name,
            metadata={
                "landed": filename in extracted,
                "output_file": MetadataValue.path(str(out_dir / filename)),
            },
        )


@asset(group_name="bronze", retry_policy=RetryPolicy(max_retries=1, delay=60))
def raw_stops_by_route(context: AssetExecutionContext, septa_api: SeptaApiResource) -> None:
    """Daily: stop id/name/lat/lon per route_id actually seen live over the
    prior day, via the Stops API - covers ad-hoc routes GTFS never knew
    about. Reads route_ids directly from the bronze TransitViewAll files
    (not the shared DuckDB file), so this never contends with the
    single-writer dbt/DuckDB connection.
    """
    raw_path = raw_data_path()
    glob_pattern = str(Path(raw_path) / "transitview_all" / "dt=*" / "*.json.gz").replace("\\", "/")

    try:
        rows = duckdb.sql(
            f"select distinct route_id from read_json_auto('{glob_pattern}') "
            "where route_id is not null"
        ).fetchall()
        route_ids = sorted(r[0] for r in rows)
    except duckdb.IOException:
        context.log.warning("No transitview_all bronze files found yet; skipping stops refresh.")
        route_ids = []

    dt_folder = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    failures = []
    fetched = 0

    with septa_api.get_client() as client:
        for route_id in route_ids:
            try:
                stops_payload = client.get_stops_by_route(route_id)
            except Exception as exc:
                context.log.warning(f"Stops fetch failed for route {route_id}: {exc}")
                failures.append(route_id)
                continue

            records = normalize_stops_by_route(route_id, stops_payload)
            if records:
                out_dir = Path(raw_path) / "stops_by_route" / f"dt={dt_folder}" / f"route={route_id}"
                out_dir.mkdir(parents=True, exist_ok=True)
                file_name = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json.gz"
                with gzip.open(out_dir / file_name, "wt", encoding="utf-8") as f:
                    json.dump(records, f)
                fetched += 1

            # Pace requests: ~124 routes/day is a trivial load, but spacing
            # calls keeps this a well-behaved API consumer.
            time.sleep(random.uniform(0.3, 0.8))

    context.add_output_metadata(
        {
            "routes_considered": len(route_ids),
            "routes_fetched": fetched,
            "routes_failed": MetadataValue.json(failures),
        }
    )
