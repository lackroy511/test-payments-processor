from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parent / ".env",
        extra="ignore",
    )

    base_dir: Path = BASE_DIR
    log_level: str

    postgres_db: str
    postgres_user: str
    postgres_password: str
    db_host: str
    db_port: int

    access_api_key: str
    access_api_name: str = "X-API-Key"
    
    rabbitmq_default_user: str
    rabbitmq_default_pass: str
    rabbitmq_host: str
    rabbitmq_port: int

    @computed_field
    @property
    def db_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.db_host}:{self.db_port}/{self.postgres_db}"  # noqa: E501


settings = Settings()  # ty: ignore
