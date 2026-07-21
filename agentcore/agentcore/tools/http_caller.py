from typing import Any

import httpx

from agentcore.domain.services.url_scope_policy import check_url_scope

DEFAULT_TIMEOUT = 10.0


async def call_http(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    check_url_scope(url, run_id)

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.request(
            method=method.upper(),
            url=url,
            headers=headers or {},
            json=body,
        )

    return {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": response.text[:5000],  # cap response size
    }
