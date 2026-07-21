from agentcore.domain.entities import TaskResult
from agentcore.domain.services.result_summarizer import summarize_results


def test_summarize_results_includes_each_task() -> None:
    results = [
        TaskResult(task="search", tool="web_search", result={"data": "found"}, success=True),
        TaskResult(task="call api", tool="http_caller", result={"error": "timeout"}, success=False),
    ]

    summary = summarize_results(results)

    assert "search" in summary
    assert "call api" in summary


def test_summarize_results_empty_list() -> None:
    assert summarize_results([]) == ""
