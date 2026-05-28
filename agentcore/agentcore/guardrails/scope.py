from urllib.parse import urlparse

import structlog

log = structlog.get_logger()

BLOCKED_DOMAINS: set[str] = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "169.254.169.254",  # AWS metadata
    "metadata.google.internal",
}


def check_url_scope(url: str, run_id: str) -> None:
    try:
        host = urlparse(url).hostname or ""
    except Exception as exc:
        raise ScopeViolationError(f"Invalid URL: {url}") from exc

    if host in BLOCKED_DOMAINS or host.endswith(".internal"):
        log.warning("scope_violation", run_id=run_id, url=url, host=host)
        raise ScopeViolationError(f"URL {url} is in the blocked scope")


class ScopeViolationError(Exception):
    pass
