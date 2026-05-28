from typing import Any

import structlog

from agentcore.eval.adversarial import ADVERSARIAL_CASES
from agentcore.eval.report import generate_report

log = structlog.get_logger()


async def run_eval_suite(eval_id: str, target_model: str, categories: list[str]) -> dict[str, Any]:
    log.info("eval_started", eval_id=eval_id, model=target_model, categories=categories)

    cases = [c for c in ADVERSARIAL_CASES if c["category"] in categories]
    results = []

    for case in cases:
        # TODO: run case against live agent and check response
        result = {
            "category": case["category"],
            "input": case["input"],
            "passed": False,
            "response": None,
            "error": "eval not yet implemented",
        }
        results.append(result)

    report = generate_report(eval_id, results)
    log.info("eval_finished", eval_id=eval_id, score=report["score"])
    return report
