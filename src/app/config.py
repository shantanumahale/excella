from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Postgres / TimescaleDB
    database_url: str = "postgresql://excella:excella_dev@localhost:5432/excella"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # RabbitMQ
    rabbitmq_url: str = "amqp://excella:excella_dev@localhost:5672/"

    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9200"

    # S3 / MinIO
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "excella"
    s3_secret_key: str = "excella_dev_key"
    s3_bucket: str = "excella-raw"

    # SEC EDGAR
    edgar_user_agent: str = "Excella dev@example.com"

    # FRED
    fred_api_key: str = ""

    # Auth / JWT
    jwt_secret: str = "excella-dev-secret-change-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # App
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
