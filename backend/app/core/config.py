from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration, loaded from environment variables / .env"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = ""
    groq_model: str = "gemma2-9b-it"
    groq_context_model: str = "llama-3.3-70b-versatile"

    database_url: str = "sqlite:///./aivoa_complaints.db"
    frontend_origin: str = "http://localhost:5173"

    # Below this similarity score, two complaints are not considered duplicates.
    duplicate_similarity_threshold: float = 0.72


@lru_cache
def get_settings() -> Settings:
    return Settings()
