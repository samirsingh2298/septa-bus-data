with source as (
    select * from {{ source('bronze', 'transitview_all_raw') }}
)

select
    route_id,
    vehicle_id,
    block_id,
    direction,
    destination,
    {{ filter_sentinel_late('late') }} as minutes_late,
    try_cast(lat as double) as lat,
    try_cast(lon as double) as lon,
    try_cast(heading as integer) as heading,
    trip_id,
    next_stop_id,
    next_stop_name,
    try_cast(next_stop_sequence as integer) as next_stop_sequence,
    to_timestamp(try_cast(vehicle_timestamp_epoch as bigint)) as vehicle_timestamp,
    try_cast(ingested_at as timestamp) as ingested_at,
    filename as source_file
from source
where vehicle_id is not null
  and route_id is not null
