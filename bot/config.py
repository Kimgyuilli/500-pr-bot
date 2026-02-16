from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    github_token: str
    github_repo: str
    github_base_branch: str = "main"
    base_package: str
    discord_webhook_url: str
    bot_port: int = 8000

    model_config = {"env_file": ".env"}


settings = Settings()
