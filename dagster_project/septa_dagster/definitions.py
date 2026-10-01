from dagster import Definitions
from dagster_dbt import DbtCliResource

from .assets.bronze_assets import raw_gtfs_snapshot, raw_stops_by_route, raw_transitview_all_snapshot
from .assets.dbt_assets import dbt_project, septa_dbt_assets
from .jobs import gtfs_refresh_job, poll_and_transform_job, stops_refresh_job
from .resources import SeptaApiResource
from .schedules import gtfs_refresh_schedule, poll_schedule, stops_refresh_schedule

defs = Definitions(
    assets=[
        raw_transitview_all_snapshot,
        raw_gtfs_snapshot,
        raw_stops_by_route,
        septa_dbt_assets,
    ],
    jobs=[poll_and_transform_job, gtfs_refresh_job, stops_refresh_job],
    schedules=[poll_schedule, gtfs_refresh_schedule, stops_refresh_schedule],
    resources={
        "septa_api": SeptaApiResource(),
        "dbt": DbtCliResource(
            project_dir=dbt_project.project_dir,
            profiles_dir=dbt_project.project_dir,
        ),
    },
)
