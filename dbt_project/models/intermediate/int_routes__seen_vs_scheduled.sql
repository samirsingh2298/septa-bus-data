with seen as (
    select distinct route_id
    from {{ ref('stg_transitview_all__vehicle_positions') }}
    where route_id is not null
),

scheduled as (
    select * from {{ ref('stg_gtfs__routes') }}
)

select
    seen.route_id,
    scheduled.route_short_name,
    scheduled.route_long_name,
    scheduled.route_type,
    scheduled.route_id is not null as is_scheduled_route
from seen
left join scheduled
    on seen.route_id = scheduled.route_id
