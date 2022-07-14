from typing import List

from pydantic import BaseSettings
from yarl import URL


class Settings(BaseSettings):
    """Application settings."""

    service_name: str = "core-commerce-coupon"

    host: str
    port: int

    # quantity of workers for uvicorn
    workers_count: int

    # Enable uvicorn reloading
    reload: bool

    db_host: str
    db_port: int
    db_user: str
    db_pass: str
    db_base: str
    db_echo: bool

    api_key: str
    backend_cors_origins: List[str] = []

    timezone: str

    log_level: str = "INFO"
    json_logs: bool = True

    # aws variables
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region_name: str = ""
    aws_s3_bucket: str = ""

    @property
    def db_url(self) -> URL:
        """
        Assemble database URL from settings.

        :return: database URL.
        """
        return URL.build(
            scheme="postgresql+asyncpg",
            host=self.db_host,
            port=self.db_port,
            user=self.db_user,
            password=self.db_pass,
            path=f"/{self.db_base}",
        )

    @property
    def db_url_alembic(self) -> URL:
        """
        Assemble database URL from settings.

        :return: database URL.
        """
        return URL.build(
            scheme="postgresql",
            host=self.db_host,
            port=self.db_port,
            user=self.db_user,
            password=self.db_pass,
            path=f"/{self.db_base}",
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "CORE_COMMERCE_COUPON_"


settings = Settings()
