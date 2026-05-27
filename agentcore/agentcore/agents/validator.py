from typing import Any

import structlog
from langchain_openai import ChatOpenAI

from agentcore.config import settings

log = structlog.get_logger()

VALIDATOR_SYSTEM = """You are a result validator. Given a task and its result, decide:
- "complete": the task is done and the result is satisfactory
- "retry": the result is incomplete or wrong, retry with adjusted approach
- "fail": the task cannot be completed

Respond as JSON: {"decision": "complete|retry|fail", "reason": "..."}"""


def build_validator(model: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base=settings.openrouter_base_url,
        max_tokens=300,
    )


async def validate_result(task: str, result: Any, model: str, run_id: str) -> dict:
    log.info("validating_result", run_id=run_id, task=task[:80])
    validator = build_validator(model)
    response = await validator.ainvoke([
        {"role": "system", "content": VALIDATOR_SYSTEM},
        {"role": "user", "content": f"Task: {task}\nResult: {str(result)[:500]}"},
    ])
    return {"decision": "complete", "reason": response.content}
