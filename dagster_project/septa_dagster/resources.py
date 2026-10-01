import os

from dagster import ConfigurableResource
from septa_client import SeptaClient


class SeptaApiResource(ConfigurableResource):
    base_url: str = os.environ.get("SEPTA_API_BASE_URL", "https://www3.septa.org")
    timeout_seconds: float = float(os.environ.get("SEPTA_HTTP_TIMEOUT_SECONDS", "10"))
    max_retries: int = int(os.environ.get("SEPTA_MAX_RETRIES", "3"))

    def get_client(self) -> SeptaClient:
        return SeptaClient(
            base_url=self.base_url,
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
        )
