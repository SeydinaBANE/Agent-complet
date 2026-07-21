from agentcore.domain.entities import TaskResult


def summarize_results(results: list[TaskResult]) -> str:
    return "\n".join(
        f"- {r['task']}: {'✓' if r['success'] else '✗'} {str(r['result'])[:200]}" for r in results
    )
