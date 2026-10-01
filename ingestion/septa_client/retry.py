import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_random_exponential


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return False


def with_retry(max_attempts: int = 3):
    return retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(max_attempts),
        wait=wait_random_exponential(multiplier=0.5, max=10),
        reraise=True,
    )
