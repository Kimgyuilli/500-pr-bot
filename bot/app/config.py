from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    github_token: str
    github_repo: str
    github_base_branch: str = "main"
    base_package: str
    discord_webhook_url: str
    bot_port: int = 8000
    import_depth: int = 1
    ai_provider: str = "openai"
    source_mode: str = "github"
    local_source_path: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
