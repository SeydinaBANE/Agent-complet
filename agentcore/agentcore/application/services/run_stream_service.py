from collections.abc import AsyncGenerator
from typing import Any

from agentcore.ports.pubsub_port import PubSubPort


class RunStreamService:
    def __init__(self, pubsub: PubSubPort) -> None:
        self._pubsub = pubsub

    def subscribe(self, run_id: str) -> AsyncGenerator[dict[str, Any], None]:
        return self._pubsub.subscribe(run_id)
