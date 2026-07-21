import pytest

from agentcore.domain.errors import MaxIterationsError
from agentcore.domain.services.iteration_policy import check_iterations


def test_iterations_not_exceeded() -> None:
    check_iterations(5, 10, "run-1")  # should not raise


def test_iterations_exceeded() -> None:
    with pytest.raises(MaxIterationsError):
        check_iterations(10, 10, "run-1")
