from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    headers: dict[str, str]
    body: str


class HttpClientPort(Protocol):
    async def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None,
        body: dict[str, Any] | None,
        timeout: float,
    ) -> HttpResponse: ...
