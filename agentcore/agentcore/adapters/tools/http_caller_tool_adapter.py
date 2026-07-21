from typing import Any

from agentcore.domain.services.url_scope_policy import check_url_scope
from agentcore.ports.http_client_port import HttpClientPort

DEFAULT_TIMEOUT = 10.0


class HttpCallerToolAdapter:
    name = "http_caller"

    def __init__(self, http_client: HttpClientPort) -> None:
        self._http_client = http_client

    async def run(self, tool_input: dict[str, Any], run_id: str) -> Any:
        url = str(tool_input.get("url", ""))
        check_url_scope(url, run_id)

        response = await self._http_client.request(
            method=str(tool_input.get("method", "GET")),
            url=url,
            headers=tool_input.get("headers"),
            body=tool_input.get("body"),
            timeout=DEFAULT_TIMEOUT,
        )
        return {
            "status_code": response.status_code,
            "headers": response.headers,
            "body": response.body,
        }
