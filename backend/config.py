"""Application configuration using Pydantic Settings."""
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "agentops"
    db_password: str = "agentops_dev_password"
    db_name: str = "agentops_db"

    # App
    app_env: str = "development"
    app_debug: bool = True

    model_config = ConfigDict(env_file=".env", case_sensitive=False)

    @property
    def database_url(self) -> str:
        """Construct database URL from components."""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
