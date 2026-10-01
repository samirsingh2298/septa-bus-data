import httpx
import pytest
import respx

from septa_client.client import SeptaClient

BASE_URL = "https://www3.septa.org"


@respx.mock
def test_get_transitview_all_passes_through_sentinel_late_values():
    route = respx.get(f"{BASE_URL}/api/TransitViewAll/")
    route.mock(
        return_value=httpx.Response(
            200,
            json={
                "routes": [
                    {
                        "route_id": "17",
                        "bus": [
                            {"vehicle_id": "1234", "late": 7},
                            {"vehicle_id": "5678", "late": 998},
                            {"vehicle_id": "9012", "late": -2},
                        ],
                    }
                ]
            },
        )
    )

    with SeptaClient(base_url=BASE_URL) as client:
        payload = client.get_transitview_all()

    assert route.called
    late_values = [v["late"] for v in payload["routes"][0]["bus"]]
    assert late_values == [7, 998, -2]


@respx.mock
def test_get_stops_by_route_passes_route_id_param():
    route = respx.get(f"{BASE_URL}/api/Stops/index.php").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"stopid": "1001", "stopname": "Broad & Market", "lat": "39.95", "lon": "-75.16"}
            ],
        )
    )

    with SeptaClient(base_url=BASE_URL) as client:
        stops = client.get_stops_by_route("17")

    assert route.calls.last.request.url.params["req1"] == "17"
    assert stops[0]["stopid"] == "1001"


@respx.mock
def test_get_transitview_all_retries_on_server_error_then_succeeds():
    route = respx.get(f"{BASE_URL}/api/TransitViewAll/")
    route.side_effect = [
        httpx.Response(503),
        httpx.Response(200, json={"routes": []}),
    ]

    with SeptaClient(base_url=BASE_URL, max_retries=3) as client:
        payload = client.get_transitview_all()

    assert payload == {"routes": []}
    assert route.call_count == 2


@respx.mock
def test_get_transitview_all_does_not_retry_on_client_error():
    route = respx.get(f"{BASE_URL}/api/TransitViewAll/").mock(return_value=httpx.Response(404))

    with SeptaClient(base_url=BASE_URL, max_retries=3) as client:
        with pytest.raises(httpx.HTTPStatusError):
            client.get_transitview_all()

    assert route.call_count == 1


@respx.mock
def test_get_transitview_all_raises_after_exhausting_retries_on_timeout():
    route = respx.get(f"{BASE_URL}/api/TransitViewAll/")
    route.side_effect = httpx.TimeoutException("timed out")

    with SeptaClient(base_url=BASE_URL, max_retries=3) as client:
        with pytest.raises(httpx.TimeoutException):
            client.get_transitview_all()

    assert route.call_count == 3


@respx.mock
def test_get_gtfs_feed_bytes_returns_zip_content():
    fake_zip_bytes = b"PK\x03\x04fake-zip-content"
    respx.get(f"{BASE_URL}/developer/gtfs_public.zip").mock(
        return_value=httpx.Response(200, content=fake_zip_bytes)
    )

    with SeptaClient(base_url=BASE_URL) as client:
        content = client.get_gtfs_feed_bytes()

    assert content == fake_zip_bytes
