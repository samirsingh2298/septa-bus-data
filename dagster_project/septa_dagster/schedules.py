import os

from dagster import DefaultScheduleStatus, ScheduleDefinition

from .jobs import gtfs_refresh_job, poll_and_transform_job, stops_refresh_job

# default_status=RUNNING so the pipeline starts polling automatically on
# `docker compose up` rather than requiring someone to flip each schedule on
# in Dagit first.
poll_schedule = ScheduleDefinition(
    job=poll_and_transform_job,
    cron_schedule=os.environ.get("POLL_CRON", "*/5 * * * *"),
    default_status=DefaultScheduleStatus.RUNNING,
)

# Weekly, off-peak: route/stop reference data changes rarely.
gtfs_refresh_schedule = ScheduleDefinition(
    job=gtfs_refresh_job,
    cron_schedule="0 4 * * 1",
    default_status=DefaultScheduleStatus.RUNNING,
)

# Daily, off-peak: refreshes stop lists for every route_id seen live
# yesterday, including any ad-hoc route that newly appeared.
stops_refresh_schedule = ScheduleDefinition(
    job=stops_refresh_job,
    cron_schedule="30 3 * * *",
    default_status=DefaultScheduleStatus.RUNNING,
)
