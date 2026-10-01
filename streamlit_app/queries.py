import pandas as pd

from db import query


def route_list() -> pd.DataFrame:
    """Only routes with at least one stop (this app is a stop-click map, so a
    route with no stops has nothing to show). Numeric route_ids first,
    ascending by value; letter-prefixed route_ids (e.g. B1/L1/T1/T2/T4) after,
    sorted alphabetically.
    """
    return query(
        """
        select route_id, route_short_name, route_long_name, is_scheduled_route
        from dim_route
        where route_id in (select distinct route_id from dim_stop)
        order by
            case when regexp_matches(route_id, '^[0-9]+$') then 0 else 1 end,
            case when regexp_matches(route_id, '^[0-9]+$') then cast(route_id as integer) end,
            route_id
        """
    )


def route_shape(route_id: str) -> pd.DataFrame:
    """A route commonly has multiple shape_ids (inbound/outbound/branches) -
    callers must draw each shape_id as its own line segment, not one
    continuous line, or unrelated paths get connected together."""
    return query(
        """
        select shape_id, shape_pt_sequence, shape_pt_lat, shape_pt_lon
        from dim_route_shape
        where route_id = ?
        order by shape_id, shape_pt_sequence
        """,
        [route_id],
    )


def stop_lateness_for_route(route_id: str) -> pd.DataFrame:
    """Stop name/lat/lon plus average lateness over all available history,
    weighted by known-late count so days with more observations count more.
    Covers ad-hoc routes too, since dim_stop is built from the Stops API
    (not GTFS) and so has no scheduled-route dependency.
    """
    return query(
        """
        select
            s.stop_id,
            s.stop_name,
            s.lat,
            s.lon,
            sum(a.avg_minutes_late * a.known_late_count) / sum(a.known_late_count) as avg_minutes_late,
            sum(a.observation_count) as observation_count,
            sum(a.known_late_count) as known_late_count
        from dim_stop s
        left join agg_lateness_by_route_stop_daily a
            on a.route_id = s.route_id and a.stop_id = s.stop_id and a.known_late_count > 0
        where s.route_id = ?
        group by s.stop_id, s.stop_name, s.lat, s.lon
        """,
        [route_id],
    )
