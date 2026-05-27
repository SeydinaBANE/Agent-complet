from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenRouter
    openrouter_api_key: str
    openrouter_default_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Security
    agentcore_api_key: str

    # CORS
    flowrunner_origin: str = "http://localhost:5173"

    # Agent defaults
    default_max_iterations: int = 10
    default_budget_usd: float = 0.10
    default_max_tokens: int = 4000


settings = Settings()  # type: ignore[call-arg]
