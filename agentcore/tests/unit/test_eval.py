from agentcore.eval.report import generate_report, report_to_html


def _make_result(category: str, passed: bool) -> dict:
    return {"category": category, "input": "test input", "passed": passed, "response": None}


def test_perfect_score() -> None:
    results = [_make_result("reliability", True) for _ in range(5)]
    report = generate_report("eval-1", results)
    assert report["score"] == 100.0
    assert report["passed"] == 5
    assert report["failed"] == 0


def test_zero_score() -> None:
    results = [_make_result("prompt_injection", False) for _ in range(3)]
    report = generate_report("eval-1", results)
    assert report["score"] == 0.0
    assert report["failed"] == 3


def test_partial_score() -> None:
    results = [_make_result("reliability", True), _make_result("jailbreak", False)]
    report = generate_report("eval-1", results)
    assert report["score"] == 50.0


def test_empty_results() -> None:
    report = generate_report("eval-1", [])
    assert report["score"] == 0.0
    assert report["total"] == 0


def test_by_category_breakdown() -> None:
    results = [
        _make_result("reliability", True),
        _make_result("reliability", False),
        _make_result("prompt_injection", True),
    ]
    report = generate_report("eval-1", results)
    assert report["by_category"]["reliability"]["total"] == 2
    assert report["by_category"]["reliability"]["passed"] == 1
    assert report["by_category"]["prompt_injection"]["passed"] == 1


def test_html_report_contains_score() -> None:
    report = generate_report("eval-42", [_make_result("reliability", True)])
    html = report_to_html(report)
    assert "100.0/100" in html
    assert "eval-42" in html
    assert "PASS" in html


def test_html_report_shows_fail() -> None:
    report = generate_report("eval-42", [_make_result("jailbreak", False)])
    html = report_to_html(report)
    assert "FAIL" in html
