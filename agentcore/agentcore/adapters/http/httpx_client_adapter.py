from typing import Any

import httpx

from agentcore.ports.http_client_port import HttpResponse

DEFAULT_TIMEOUT = 10.0
MAX_BODY_LENGTH = 5000
MAX_RETRIES = 3

_client: httpx.AsyncClient | None = None


async def _get_client(timeout: float = DEFAULT_TIMEOUT) -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _client


async def close_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None


class HttpxClientAdapter:
    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    async def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> HttpResponse:
        client = await _get_client(timeout or self._timeout)

        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers or {},
                    json=body,
                )
                return HttpResponse(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=response.text[:MAX_BODY_LENGTH],
                )
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt == MAX_RETRIES - 1:
                    raise
        raise last_exc  # type: ignore[misc]
