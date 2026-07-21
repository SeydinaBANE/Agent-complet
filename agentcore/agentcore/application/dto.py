from dataclasses import dataclass


@dataclass(frozen=True)
class AgentDefaults:
    model: str
    max_iterations: int
    max_tokens: int
    budget_usd: float
    tools: list[str]
