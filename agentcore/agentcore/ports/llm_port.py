from typing import Any, Protocol


class LlmPort(Protocol):
    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        run_id: str,
    ) -> tuple[str, int, int]: ...

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        run_id: str,
    ) -> tuple[Any, int, int]: ...
