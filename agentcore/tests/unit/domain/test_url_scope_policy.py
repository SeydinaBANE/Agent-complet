import pytest

from agentcore.domain.errors import ScopeViolationError
from agentcore.domain.services.url_scope_policy import check_url_scope


def test_scope_allows_public_url() -> None:
    check_url_scope("https://example.com/api", "run-1")  # should not raise


def test_scope_blocks_localhost() -> None:
    with pytest.raises(ScopeViolationError):
        check_url_scope("http://localhost:8080/secret", "run-1")


def test_scope_blocks_aws_metadata() -> None:
    with pytest.raises(ScopeViolationError):
        check_url_scope("http://169.254.169.254/latest/meta-data/", "run-1")
