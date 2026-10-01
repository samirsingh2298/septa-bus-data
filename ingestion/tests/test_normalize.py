from septa_client.normalize import normalize_stops_by_route, normalize_transitview_all


def test_normalizes_confirmed_live_shape():
    # Confirmed shape from a real TransitViewAll call: "routes" is a list
    # containing a single dict keyed by route_id -> list of vehicle dicts.
    payload = {
        "routes": [
            {
                "125": [
                    {
                        "lat": "39.952043",
                        "lng": "-75.165277",
                        "label": "3711",
                        "VehicleID": "3711",
                        "route_id": "125",
                        "BlockID": "4701",
                        "Direction": "EastBound",
                        "destination": "13th-Market",
                        "Offset": "-10",
                        "heading": 124,
                        "late": -10,
                        "trip": "958240",
                        "next_stop_id": "1537",
                        "next_stop_name": None,
                        "next_stop_sequence": 35,
                        "timestamp": 1790866526,
                    }
                ],
                "47": [
                    {
                        "lat": "39.945402",
                        "lng": "-75.153239",
                        "label": "3809",
                        "VehicleID": "3809",
                        "route_id": "47",
                        "late": 998,
                        "next_stop_id": "18505",
                        "next_stop_name": "7th St & Carpenter St",
                    }
                ],
            }
        ]
    }

    records = normalize_transitview_all(payload)

    assert len(records) == 2
    r125 = next(r for r in records if r["route_id"] == "125")
    assert r125["vehicle_id"] == "3711"
    assert r125["late"] == -10
    assert r125["lat"] == "39.952043"
    assert r125["lon"] == "-75.165277"
    assert r125["heading"] == 124
    assert r125["next_stop_sequence"] == 35
    assert r125["vehicle_timestamp_epoch"] == 1790866526
    assert r125["raw"]["VehicleID"] == "3711"

    r47 = next(r for r in records if r["route_id"] == "47")
    assert r47["late"] == 998
    assert r47["next_stop_name"] == "7th St & Carpenter St"


def test_vehicle_own_route_id_takes_precedence_over_outer_key():
    payload = {"routes": [{"999": [{"VehicleID": "1", "route_id": "17"}]}]}

    records = normalize_transitview_all(payload)

    assert records[0]["route_id"] == "17"


def test_normalizes_route_keyed_dict_fallback_shape():
    payload = {
        "17": [{"VehicleID": "1234", "late": -2}],
        "33": {"bus": [{"VehicleID": "9999", "late": 4}]},
    }

    records = normalize_transitview_all(payload)
    route_ids = sorted(r["route_id"] for r in records)

    assert route_ids == ["17", "33"]
    assert len(records) == 2


def test_normalizes_flat_list_fallback_shape():
    payload = [
        {"route": "17", "VehicleID": "1234", "late": 1},
        {"route": "33", "VehicleID": "5678", "late": 2},
    ]

    records = normalize_transitview_all(payload)

    assert len(records) == 2
    assert {r["route_id"] for r in records} == {"17", "33"}


def test_unrecognized_shape_returns_empty_list_without_raising():
    assert normalize_transitview_all(42) == []
    assert normalize_transitview_all(None) == []


def test_normalize_stops_by_route_flattens_fields():
    # Confirmed live shape from the Stops API: flat list of {lng, lat, stopid, stopname}
    payload = [
        {"lng": "-75.142317", "lat": "39.949765", "stopid": "69", "stopname": "Front St & Market St Loop"},
        {"lng": "-75.177411", "lat": "39.926716", "stopid": "21333", "stopname": "19th St & McKean St"},
    ]

    records = normalize_stops_by_route("17", payload)

    assert len(records) == 2
    assert records[0]["route_id"] == "17"
    assert records[0]["stop_id"] == "69"
    assert records[0]["stop_name"] == "Front St & Market St Loop"
    assert records[0]["lon"] == "-75.142317"
    assert records[1]["stop_id"] == "21333"


def test_normalize_stops_by_route_non_list_returns_empty():
    assert normalize_stops_by_route("17", {"error": "bad route"}) == []
