with source as (
    select * from {{ source('bronze', 'stops_by_route_raw') }}
),

ranked as (
    select
        *,
        row_number() over (partition by route_id, stop_id order by dt desc) as rn
    from source
)

select
    route_id,
    stop_id,
    stop_name,
    try_cast(lat as double) as lat,
    try_cast(lon as double) as lon
from ranked
where rn = 1
  and stop_id is not null
