from functools import lru_cache
import os

from pydantic import SecretStr, Field
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

    # AWS settings for S3 fetcher
    aws_access_key_id: str | None = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_default_region: str = Field(default="us-east-1", env="AWS_DEFAULT_REGION")

    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.aws_access_key_id:
            self.aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        if not self.aws_secret_access_key:
            self.aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        if not self.aws_default_region or self.aws_default_region == "us-east-1":
            self.aws_default_region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')


@lru_cache()
def get_settings():
    return Settings()
