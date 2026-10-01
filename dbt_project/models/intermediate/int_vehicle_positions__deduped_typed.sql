with staged as (
    select * from {{ ref('stg_transitview_all__vehicle_positions') }}
),

deduped as (
    select
        *,
        row_number() over (
            partition by vehicle_id, trip_id, ingested_at
            order by source_file
        ) as rn
    from staged
)

select
    route_id,
    vehicle_id,
    block_id,
    direction,
    destination,
    minutes_late,
    minutes_late is not null as is_late_known,
    lat,
    lon,
    heading,
    trip_id,
    next_stop_id,
    next_stop_name,
    next_stop_sequence,
    vehicle_timestamp,
    ingested_at,
    source_file
from deduped
where rn = 1
