{{ config(materialized='table') }}

-- Small aggregate recomputed fully each run; full history matters here for
-- stable hour-of-day/day-of-week patterns, so incremental isn't worth the
-- complexity. ingested_at is stored UTC; converted to US/Eastern here for a
-- Philadelphia audience.
select
    route_id,
    extract(hour from ingested_at at time zone 'America/New_York') as hour_of_day,
    extract(dow from ingested_at at time zone 'America/New_York') as day_of_week,
    avg(minutes_late) filter (where is_late_known) as avg_minutes_late,
    count(*) as observation_count
from {{ ref('fct_vehicle_observations') }}
group by route_id, hour_of_day, day_of_week
