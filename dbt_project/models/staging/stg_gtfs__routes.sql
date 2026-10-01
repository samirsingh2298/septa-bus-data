with source as (
    select * from {{ source('bronze', 'gtfs_routes_raw') }}
),

ranked as (
    select
        *,
        row_number() over (partition by route_id order by dt desc) as rn
    from source
)

select
    route_id,
    route_short_name,
    route_long_name,
    route_type
from ranked
where rn = 1
