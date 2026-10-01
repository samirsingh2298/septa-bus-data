with source as (
    select * from {{ source('bronze', 'gtfs_trips_raw') }}
),

ranked as (
    select
        *,
        row_number() over (partition by route_id, shape_id order by dt desc) as rn
    from source
)

select distinct
    route_id,
    shape_id
from ranked
where rn = 1
  and shape_id is not null
