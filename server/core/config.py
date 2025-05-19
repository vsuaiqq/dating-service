from pydantic_settings import BaseSettings
from pydantic import RedisDsn, PostgresDsn, Field
from typing import List
from functools import lru_cache

class Settings(BaseSettings):

    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    DB_HOST: str
    DB_PORT: int

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_FASTAPI_CACHE: int
    REDIS_CELERY: int
    REDIS_LIMITER: int

    KAFKA_HOST: str
    KAFKA_PORT: int
    KAFKA_SWIPES_TOPIC: str
    KAFKA_GEO_TOPIC: str
    KAFKA_VIDEO_TOPIC: str
    KAFKA_GEO_NOTIFICATIONS_TOPIC: str
    KAFKA_VIDEO_NOTIFICATIONS_TOPIC: str
    
    S3_ENDPOINT_URL: str
    S3_REGION_NAME: str
    S3_BUCKET_NAME: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str

    CLICKHOUSE_HOST: str
    CLICKHOUSE_PORT: int
    CLICKHOUSE_DB: str
    CLICKHOUSE_USER: str
    CLICKHOUSE_PASSWORD: str

    API_SECRET_KEY: str

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    ORIGINS: List[str] = Field(default_factory=lambda: [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ])

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def postgres_dsn(self) -> PostgresDsn:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"

    @property
    def redis_url_cache(self) -> RedisDsn:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_FASTAPI_CACHE}"

    @property
    def redis_url_celery(self) -> RedisDsn:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_CELERY}"
    
    @property
    def redis_url_limiter(self) -> RedisDsn:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_LIMITER}"

    @property
    def kafka_bootstrap_servers(self) -> str:
        return f"{self.KAFKA_HOST}:{self.KAFKA_PORT}"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
