import hmac

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from agentcore.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


def require_api_key(key: str = Security(api_key_header)) -> str:
    if not hmac.compare_digest(key, settings.agentcore_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return key
