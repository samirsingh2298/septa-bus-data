-- Road-path polyline per route, scheduled routes only (ad-hoc routes have no
-- GTFS shape; the live map falls back to stop points + vehicle positions for
-- those, see dim_stop).
with trips as (
    select distinct route_id, shape_id from {{ ref('stg_gtfs__trips') }}
),

shapes as (
    select * from {{ ref('stg_gtfs__shapes') }}
)

select
    trips.route_id,
    shapes.shape_id,
    shapes.shape_pt_sequence,
    shapes.shape_pt_lat,
    shapes.shape_pt_lon
from trips
inner join shapes
    on trips.shape_id = shapes.shape_id
-- A route commonly has multiple shape_ids (inbound/outbound/branches), and
-- shape_pt_sequence restarts at 1 for each one - order by shape_id first so
-- each shape's points stay contiguous instead of interleaving by sequence
-- number across unrelated physical paths (which drew zigzag lines on the map).
order by trips.route_id, shapes.shape_id, shapes.shape_pt_sequence
