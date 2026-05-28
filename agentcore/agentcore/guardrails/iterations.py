import structlog

log = structlog.get_logger()


def check_iterations(current: int, max_iterations: int, run_id: str) -> None:
    if current >= max_iterations:
        log.warning("max_iterations_reached", run_id=run_id, iterations=current)
        raise MaxIterationsError(f"Run {run_id} reached max iterations ({max_iterations})")


class MaxIterationsError(Exception):
    pass
