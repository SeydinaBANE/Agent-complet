from typing import Any

import httpx

from agentcore.ports.http_client_port import HttpResponse

DEFAULT_TIMEOUT = 10.0
MAX_BODY_LENGTH = 5000


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
        async with httpx.AsyncClient(timeout=timeout or self._timeout) as client:
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
