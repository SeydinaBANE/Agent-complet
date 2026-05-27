import json
from typing import Any

import structlog
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from agentcore.config import settings

log = structlog.get_logger()


def _make_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
async def chat(
    messages: list[dict[str, str]],
    model: str,
    max_tokens: int = 1000,
    run_id: str = "",
) -> tuple[str, int, int]:
    """Returns (content, input_tokens, output_tokens)."""
    client = _make_client()
    response = await client.chat.completions.create(
        model=model,
        messages=messages,  # type: ignore[arg-type]
        max_tokens=max_tokens,
    )
    usage = response.usage
    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0
    content = response.choices[0].message.content or ""
    log.info(
        "llm_call",
        run_id=run_id,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    return content, input_tokens, output_tokens


async def chat_json(
    messages: list[dict[str, str]],
    model: str,
    max_tokens: int = 1000,
    run_id: str = "",
) -> tuple[Any, int, int]:
    """Call LLM and parse JSON response."""
    content, input_t, output_t = await chat(messages, model, max_tokens, run_id)
    try:
        # Strip markdown code fences if present
        clean = content.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(clean), input_t, output_t
    except json.JSONDecodeError as err:
        log.warning("llm_json_parse_error", run_id=run_id, content=content[:200])
        raise ValueError(f"LLM did not return valid JSON: {content[:200]}") from err
