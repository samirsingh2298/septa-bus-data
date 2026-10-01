"""Flattens TransitViewAll's response into one flat dict per vehicle.

Confirmed against a live call (2026-10-01): the response is
    {"routes": [{"<route_id>": [<vehicle>, ...], "<route_id2>": [...], ...}]}
i.e. "routes" is a list containing a single dict keyed by route_id, each value
a list of vehicle dicts. Each vehicle dict already carries its own "route_id"
field too, which takes precedence over the outer grouping key. Sample vehicle
fields: lat, lng, label, VehicleID, route_id, BlockID, Direction, destination,
Offset (string), heading, late (int, 998/999 = no prediction), original_late,
Offset_sec (string), trip, next_stop_id, next_stop_name (nullable),
next_stop_sequence, estimated_seat_availability, timestamp (unix epoch
seconds, the vehicle's own GPS ping time).

A dict-keyed-by-route-id-directly fallback (no "routes" wrapper) and a flat
list-of-vehicles fallback are also handled, in case the API shape ever shifts.
"""

FIELD_ALIASES = {
    "vehicle_id": ("VehicleID", "vehicle_id", "label", "Label"),
    "block_id": ("BlockID", "block_id"),
    "direction": ("Direction", "direction"),
    "destination": ("destination", "Destination"),
    "late": ("late", "Late"),
    "offset_minutes": ("Offset", "offset"),
    "heading": ("heading", "Heading"),
    "lat": ("lat", "Lat", "latitude"),
    "lon": ("lng", "lon", "Lng", "Lon", "longitude"),
    "trip_id": ("trip", "TripID", "trip_id"),
    "next_stop_id": ("next_stop_id", "NextStopID", "nextstopid"),
    "next_stop_name": ("next_stop_name", "NextStopName", "nextstopname"),
    "next_stop_sequence": ("next_stop_sequence", "NextStopSequence"),
    "vehicle_timestamp_epoch": ("timestamp", "Timestamp"),
}


def _pick(vehicle: dict, field: str):
    for key in FIELD_ALIASES[field]:
        if key in vehicle:
            return vehicle[key]
    return None


def _flatten_vehicle(route_id, vehicle: dict) -> dict:
    actual_route_id = vehicle.get("route_id") or vehicle.get("RouteID") or route_id
    record = {"route_id": str(actual_route_id) if actual_route_id is not None else None}
    for field in FIELD_ALIASES:
        record[field] = _pick(vehicle, field)
    record["raw"] = vehicle
    return record


def _vehicles_from_route_bucket(bucket) -> list[dict]:
    """A per-route bucket may be a bare list of vehicles, or (fallback) a dict
    with 'bus'/'trolley' sub-lists."""
    if isinstance(bucket, list):
        return bucket
    if isinstance(bucket, dict):
        vehicles = []
        for key in ("bus", "trolley", "vehicles"):
            vehicles.extend(bucket.get(key) or [])
        return vehicles
    return []


def normalize_transitview_all(payload) -> list[dict]:
    records: list[dict] = []

    if isinstance(payload, dict) and isinstance(payload.get("routes"), list):
        # Confirmed live shape: {"routes": [{"<route_id>": [vehicle, ...], ...}]}
        for page in payload["routes"]:
            if not isinstance(page, dict):
                continue
            for route_id, bucket in page.items():
                for vehicle in _vehicles_from_route_bucket(bucket):
                    records.append(_flatten_vehicle(route_id, vehicle))
        return records

    if isinstance(payload, dict):
        # Fallback shape: {"17": [...vehicles...], "33": {"bus": [...]}, ...}
        for route_id, bucket in payload.items():
            for vehicle in _vehicles_from_route_bucket(bucket):
                records.append(_flatten_vehicle(route_id, vehicle))
        return records

    if isinstance(payload, list):
        # Fallback shape: flat list of vehicles, each carrying its own route id.
        for vehicle in payload:
            route_id = vehicle.get("route") or vehicle.get("route_id") or vehicle.get("Route")
            records.append(_flatten_vehicle(route_id, vehicle))
        return records

    return records


STOP_FIELD_ALIASES = {
    "stop_id": ("stopid", "StopId", "STOPID", "stop_id"),
    "stop_name": ("stopname", "StopName", "STOPNAME", "stop_name"),
    "lat": ("lat", "Lat", "LAT", "latitude"),
    "lon": ("lon", "Lon", "LON", "lng", "Lng", "longitude"),
}


def _pick_stop(stop: dict, field: str):
    for key in STOP_FIELD_ALIASES[field]:
        if key in stop:
            return stop[key]
    return None


def normalize_stops_by_route(route_id: str, payload) -> list[dict]:
    """Flattens the Stops API response for one route into canonical records."""
    if not isinstance(payload, list):
        return []

    records = []
    for stop in payload:
        if not isinstance(stop, dict):
            continue
        record = {"route_id": str(route_id)}
        for field in STOP_FIELD_ALIASES:
            record[field] = _pick_stop(stop, field)
        record["raw"] = stop
        records.append(record)
    return records
