with source as (
    select * from {{ source('bronze', 'gtfs_shapes_raw') }}
),

ranked as (
    select
        *,
        row_number() over (partition by shape_id, shape_pt_sequence order by dt desc) as rn
    from source
)

select
    shape_id,
    try_cast(shape_pt_lat as double) as shape_pt_lat,
    try_cast(shape_pt_lon as double) as shape_pt_lon,
    try_cast(shape_pt_sequence as integer) as shape_pt_sequence
from ranked
where rn = 1
