from datetime import datetime
from typing import Any


def generate_report(eval_id: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    score = round((passed / total * 100) if total else 0, 1)

    by_category: dict[str, dict[str, Any]] = {}
    for r in results:
        cat = r.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = {"total": 0, "passed": 0}
        by_category[cat]["total"] += 1
        if r.get("passed"):
            by_category[cat]["passed"] += 1

    return {
        "eval_id": eval_id,
        "generated_at": datetime.utcnow().isoformat(),
        "score": score,
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "by_category": by_category,
        "cases": results,
    }


def report_to_html(report: dict[str, Any]) -> str:
    score = report["score"]
    color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 50 else "#ef4444"
    cases_html = "".join(
        f"<tr><td>{c['category']}</td><td>{c['input'][:60]}</td>"
        f'<td style="color:{"green" if c["passed"] else "red"}">'
        f"{'PASS' if c['passed'] else 'FAIL'}</td></tr>"
        for c in report["cases"]
    )
    return f"""<!DOCTYPE html>
<html><head><title>AgentCore Eval — {report["eval_id"]}</title></head>
<body style="font-family:sans-serif;max-width:800px;margin:40px auto">
<h1>Eval Report</h1>
<p>ID: {report["eval_id"]} | Generated: {report["generated_at"]}</p>
<h2 style="color:{color}">Score: {score}/100</h2>
<p>{report["passed"]}/{report["total"]} tests passed</p>
<table border="1" cellpadding="8" style="width:100%;border-collapse:collapse">
<tr><th>Category</th><th>Input</th><th>Result</th></tr>
{cases_html}
</table>
</body></html>"""
