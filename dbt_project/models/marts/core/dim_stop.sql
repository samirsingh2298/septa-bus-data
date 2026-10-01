select
    route_id,
    stop_id,
    stop_name,
    lat,
    lon
from {{ ref('stg_septa__stops_by_route') }}
