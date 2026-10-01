from dagster import AssetSelection, define_asset_job

from .assets.bronze_assets import raw_gtfs_snapshot, raw_stops_by_route

# Every 5-minute tick: poll TransitViewAll, then run the full dbt DAG
# (staging through gold). Excludes the GTFS/Stops bronze assets, which have
# their own slower schedules below - the dbt rebuild still picks up whatever
# reference data they last landed.
poll_and_transform_job = define_asset_job(
    name="poll_and_transform_job",
    selection=AssetSelection.all() - AssetSelection.assets(raw_gtfs_snapshot, raw_stops_by_route),
)

gtfs_refresh_job = define_asset_job(
    name="gtfs_refresh_job",
    selection=AssetSelection.assets(raw_gtfs_snapshot),
)

stops_refresh_job = define_asset_job(
    name="stops_refresh_job",
    selection=AssetSelection.assets(raw_stops_by_route),
)
