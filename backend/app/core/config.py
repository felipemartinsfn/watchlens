from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./watchlens.db"
    SECRET_KEY: str = "changeme-in-production"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"
    IMAGE_STORAGE_PATH: str = "./storage/images"
    MAX_UPLOAD_SIZE_MB: int = 10
    EMBEDDING_MODEL: str = "clip"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
