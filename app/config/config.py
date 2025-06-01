import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PAMP Submissions Service"
    app_version: str = "1.0.0"
    debug: bool = True

    # Server settings
    port: int = 3002

    # Database settings
    database_url: str = "postgresql://postgres:password@localhost:5432/submissions_db"
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    postgres_db: str = "submissions_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()
