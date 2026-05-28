from langchain_openai import ChatOpenAI

from agentcore.config import settings


def build_planner(model: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base=settings.openrouter_base_url,
        max_tokens=1000,
    )


PLANNER_SYSTEM = """You are a task planner. Given a goal, decompose it into 2-5 concrete,
actionable sub-tasks. Each sub-task must specify which tool to use and what input to provide.

Available tools: web_search, http_caller, memory_read, memory_write.

Respond as a JSON array: [{"task": "...", "tool": "...", "tool_input": {...}}, ...]"""
