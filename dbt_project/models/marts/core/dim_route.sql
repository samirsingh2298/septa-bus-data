select
    route_id,
    route_short_name,
    route_long_name,
    route_type,
    is_scheduled_route
from {{ ref('int_routes__seen_vs_scheduled') }}
