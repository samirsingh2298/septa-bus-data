import os

import httpx

from .retry import with_retry

DEFAULT_BASE_URL = "https://www3.septa.org"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_RETRIES = 3


class SeptaClient:
    """Thin wrapper around SEPTA's public hackathon API endpoints.

    No API key is required for any of these endpoints.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
    ):
        self.base_url = base_url or os.environ.get("SEPTA_API_BASE_URL", DEFAULT_BASE_URL)
        timeout = timeout_seconds or float(
            os.environ.get("SEPTA_HTTP_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)
        )
        self.max_retries = max_retries or int(
            os.environ.get("SEPTA_MAX_RETRIES", DEFAULT_MAX_RETRIES)
        )
        self._http = httpx.Client(base_url=self.base_url, timeout=timeout)

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def get_transitview_all(self) -> list[dict]:
        """One call returns every currently-active bus/trolley across every route."""

        @with_retry(self.max_retries)
        def _call():
            resp = self._http.get("/api/TransitViewAll/")
            resp.raise_for_status()
            return resp.json()

        return _call()

    def get_stops_by_route(self, route_id: str) -> list[dict]:
        """Stop id/name/lat/lon for a given route. Works for ad-hoc routes too,
        since it only requires a route_id string observed in the live feed,
        not a GTFS-known route.
        """

        @with_retry(self.max_retries)
        def _call():
            resp = self._http.get("/api/Stops/index.php", params={"req1": route_id})
            resp.raise_for_status()
            return resp.json()

        return _call()

    def get_gtfs_feed_bytes(self) -> bytes:
        """Downloads the static GTFS zip (routes.txt, stops.txt, trips.txt,
        stop_times.txt, shapes.txt, etc). Caller is responsible for unzipping.
        """

        @with_retry(self.max_retries)
        def _call():
            resp = self._http.get("/developer/gtfs_public.zip", follow_redirects=True)
            resp.raise_for_status()
            return resp.content

        return _call()
